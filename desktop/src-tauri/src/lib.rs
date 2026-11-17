use std::net::TcpListener;
use std::process::{Child, Command};
use std::sync::Mutex;

use tauri::{Manager, RunEvent, State};

/// The bundled Python engine (PyInstaller folder under resources/engine), started on a free
/// loopback port when the app launches and stopped when it exits. # per D-8c03
struct Engine {
    port: Option<u16>,
    child: Mutex<Option<Child>>,
}

/// Origin the UI should call; empty when no engine is bundled (`tauri dev` uses the Vite proxy).
#[tauri::command]
fn api_base(engine: State<Engine>) -> String {
    engine.port.map(|p| format!("http://127.0.0.1:{p}")).unwrap_or_default()
}

fn start_engine(app: &tauri::AppHandle) -> Engine {
    let exe = if cfg!(windows) { "lunar-eval-api.exe" } else { "lunar-eval-api" };
    let Ok(resources) = app.path().resource_dir() else {
        return Engine { port: None, child: Mutex::new(None) };
    };
    let bin = resources.join("engine").join(exe);
    if !bin.is_file() {
        return Engine { port: None, child: Mutex::new(None) };
    }
    let Ok(listener) = TcpListener::bind("127.0.0.1:0") else {
        return Engine { port: None, child: Mutex::new(None) };
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
        Ok(child) => Engine { port: Some(port), child: Mutex::new(Some(child)) },
        Err(e) => {
            eprintln!("could not start the engine: {e}");
            Engine { port: None, child: Mutex::new(None) }
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let engine = start_engine(app.handle());
            app.manage(engine);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![api_base])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                if let Some(engine) = app.try_state::<Engine>() {
                    if let Some(mut child) = engine.child.lock().unwrap().take() {
                        let _ = child.kill();
                    }
                }
            }
        });
}
