mod analyses;

use std::net::TcpListener;
use std::process::{Child, Command};
use std::sync::Mutex;

use tauri::{Manager, RunEvent, State};

/// The bundled Python engine (PyInstaller folder under resources/engine), started on a free
/// loopback port when the app launches and stopped when it exits. # per D-8c03
struct Engine {
    inner: Mutex<EngineState>,
}

#[derive(Default)]
struct EngineState {
    port: Option<u16>,
    child: Option<Child>,
    /// Why the engine could not be started (shown in the UI with a Retry button).
    error: Option<String>,
}

fn start_engine(app: &tauri::AppHandle) -> EngineState {
    let fail = |msg: String| {
        eprintln!("{msg}");
        EngineState { port: None, child: None, error: Some(msg) }
    };
    let exe = if cfg!(windows) { "moonpark-api.exe" } else { "moonpark-api" };
    let Ok(resources) = app.path().resource_dir() else {
        return EngineState::default();
    };
    let bin = resources.join("engine").join(exe);
    if !bin.is_file() {
        return EngineState::default(); // no bundled engine (`tauri dev`): the Vite proxy serves the API
    }
    let Ok(listener) = TcpListener::bind("127.0.0.1:0") else {
        return fail("no free local port for the engine".into());
    };
    let port = listener.local_addr().map(|a| a.port()).unwrap_or(0);
    drop(listener);

    let mut cmd = Command::new(&bin);
    cmd.arg("--port").arg(port.to_string());
    if let Ok(cache) = app.path().app_cache_dir() {
        let _ = std::fs::create_dir_all(&cache);
        cmd.arg("--cache").arg(cache);
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
    }
    match cmd.spawn() {
        Ok(child) => EngineState { port: Some(port), child: Some(child), error: None },
        Err(e) => fail(format!("could not start the engine ({}): {e}", bin.display())),
    }
}

/// Origin the UI should call; empty when no engine is bundled (`tauri dev` uses the Vite proxy).
#[tauri::command]
fn api_base(engine: State<Engine>) -> String {
    let st = engine.inner.lock().unwrap();
    st.port.map(|p| format!("http://127.0.0.1:{p}")).unwrap_or_default()
}

/// Empty when the engine is fine (or not bundled); otherwise a short reason it is not running.
#[tauri::command]
fn engine_status(engine: State<Engine>) -> String {
    let mut st = engine.inner.lock().unwrap();
    if let Some(e) = &st.error {
        return e.clone();
    }
    if let Some(child) = st.child.as_mut() {
        if let Ok(Some(status)) = child.try_wait() {
            let msg = format!("the engine exited unexpectedly ({status})");
            st.child = None;
            st.error = Some(msg.clone());
            return msg;
        }
    }
    String::new()
}

/// Retry: stop whatever is left of the engine and start a fresh one; returns its origin.
#[tauri::command]
fn restart_engine(app: tauri::AppHandle, engine: State<Engine>) -> String {
    let mut st = engine.inner.lock().unwrap();
    if let Some(mut child) = st.child.take() {
        let _ = child.kill();
        let _ = child.wait();
    }
    *st = start_engine(&app);
    st.port.map(|p| format!("http://127.0.0.1:{p}")).unwrap_or_default()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let engine = start_engine(app.handle());
            app.manage(Engine { inner: Mutex::new(engine) });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            api_base,
            engine_status,
            restart_engine,
            analyses::analyses_dir,
            analyses::save_analysis,
            analyses::list_analyses,
            analyses::read_analysis,
            analyses::delete_analysis
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                if let Some(engine) = app.try_state::<Engine>() {
                    if let Some(mut child) = engine.inner.lock().unwrap().child.take() {
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                }
            }
        });
}
