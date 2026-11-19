//! Saved analyses as one JSON file each in `Documents/Moonpark/`. # per D-20261118-pj-8625
//!
//! The UI owns the file content (formatVersion, id, createdAt, label, appVersion, dataVersion,
//! form, payload, summary); this module validates ids, writes atomically and lists the folder.
//! Plain std::fs, so no Tauri fs-plugin permission is involved.
//!
//! A stopped region search is kept in the same folder and envelope with `kind: "search"` and a
//! `checkpoint` (D-20261118-pj-1454); it is listed with its kind so the UI can offer Continue.

use std::fs;
use std::io::{self, Write};
use std::path::PathBuf;

use serde::Serialize;
use serde_json::Value;
use tauri::Manager;

const FOLDER: &str = "Moonpark";

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AnalysisEntry {
    id: String,
    file: String,
    created_at: String,
    label: String,
    summary: Value,
    format_version: i64,
    data_version: Option<String>,
    app_version: Option<String>,
    /// "search" for a stopped region search; absent for a site analysis.
    #[serde(skip_serializing_if = "Option::is_none")]
    kind: Option<String>,
    /// The few form inputs the list shows, copied from the file's `form` (the full form is only
    /// read when an analysis is opened). Strings as the planner form keeps them; None when absent.
    start: Option<String>,
    end: Option<String>,
    lat: Option<String>,
    lon: Option<String>,
    template_id: Option<String>,
}

#[derive(Serialize)]
pub struct AnalysisFileError {
    file: String,
    error: String,
}

#[derive(Serialize)]
pub struct AnalysisListing {
    items: Vec<AnalysisEntry>,
    errors: Vec<AnalysisFileError>,
}

fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 100
        && id.chars().all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
}

fn check_id(id: &str) -> Result<(), String> {
    if valid_id(id) {
        Ok(())
    } else {
        Err("invalid analysis id (only letters, digits, '_' and '-' are allowed)".into())
    }
}

fn io_msg(what: &str, path: &std::path::Path, e: &io::Error) -> String {
    let why = match e.kind() {
        io::ErrorKind::StorageFull => "the disk is full".to_string(),
        io::ErrorKind::PermissionDenied => "permission denied".to_string(),
        io::ErrorKind::NotFound => "not found".to_string(),
        _ => e.to_string(),
    };
    format!("{what} {}: {why}", path.display())
}

fn dir_path(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let docs = app
        .path()
        .document_dir()
        .map_err(|e| format!("cannot locate the Documents folder: {e}"))?;
    Ok(docs.join(FOLDER))
}

fn file_path(app: &tauri::AppHandle, id: &str) -> Result<PathBuf, String> {
    check_id(id)?;
    Ok(dir_path(app)?.join(format!("{id}.json")))
}

/// Folder where analyses are kept (it may not exist until the first save).
#[tauri::command]
pub async fn analyses_dir(app: tauri::AppHandle) -> Result<String, String> {
    Ok(dir_path(&app)?.display().to_string())
}

/// Write `json` (already a full analysis record) as `<id>.json`; returns the file path.
#[tauri::command]
pub async fn save_analysis(app: tauri::AppHandle, json: String, id: String) -> Result<String, String> {
    check_id(&id)?;
    let mut record: Value =
        serde_json::from_str(&json).map_err(|e| format!("the analysis is not valid JSON: {e}"))?;
    let obj = record.as_object_mut().ok_or("the analysis must be a JSON object")?;
    if obj.get("id").and_then(Value::as_str) != Some(id.as_str()) {
        return Err("the analysis id does not match its content".into());
    }
    // The app version is authoritative here, not the webview.
    obj.insert("appVersion".into(), Value::String(app.package_info().version.to_string()));
    let bytes = serde_json::to_vec(&record).map_err(|e| e.to_string())?;

    let dir = dir_path(&app)?;
    fs::create_dir_all(&dir).map_err(|e| io_msg("cannot create the folder", &dir, &e))?;
    let target = dir.join(format!("{id}.json"));
    let tmp = dir.join(format!(".{id}.json.tmp"));
    let written = (|| -> io::Result<()> {
        let mut f = fs::File::create(&tmp)?;
        f.write_all(&bytes)?;
        f.sync_all()?;
        drop(f);
        fs::rename(&tmp, &target)
    })();
    if let Err(e) = written {
        let _ = fs::remove_file(&tmp);
        return Err(io_msg("could not save", &target, &e));
    }
    Ok(target.display().to_string())
}

fn entry_from(stem: &str, file: &str, text: &str) -> Result<AnalysisEntry, String> {
    let v: Value = serde_json::from_str(text).map_err(|e| format!("not valid JSON: {e}"))?;
    let o = v.as_object().ok_or("not a JSON object")?;
    let format_version = o
        .get("formatVersion")
        .and_then(Value::as_i64)
        .ok_or("missing formatVersion")?;
    if o.get("id").and_then(Value::as_str) != Some(stem) {
        return Err("the id inside the file does not match its name".into());
    }
    if !o.get("form").is_some_and(Value::is_object) || !o.get("payload").is_some_and(Value::is_object) {
        return Err("missing form or payload".into());
    }
    let s = |k: &str| o.get(k).and_then(Value::as_str).map(str::to_string);
    let form = o.get("form").and_then(Value::as_object);
    // Form values are strings in the UI; accept a number too so a hand-edited file still lists.
    let f = |k: &str| {
        form.and_then(|m| m.get(k)).and_then(|v| match v {
            Value::String(t) => Some(t.clone()),
            Value::Number(n) => Some(n.to_string()),
            _ => None,
        })
    };
    let kind = s("kind");
    let is_search = kind.as_deref() == Some("search");
    let summary = match o.get("summary").cloned().filter(Value::is_object) {
        Some(v) => v,
        // A stopped search has no verdict yet; its summary may be minimal or absent.
        None if is_search => Value::Object(Default::default()),
        None => return Err("missing summary".into()),
    };
    Ok(AnalysisEntry {
        id: stem.to_string(),
        file: file.to_string(),
        created_at: s("createdAt").ok_or("missing createdAt")?,
        label: s("label").unwrap_or_default(),
        summary,
        format_version,
        data_version: s("dataVersion"),
        app_version: s("appVersion"),
        kind,
        start: f("start"),
        end: f("end"),
        lat: f("lat"),
        lon: f("lon"),
        template_id: f("template_id"),
    })
}

/// List every `*.json` in the folder; unreadable or invalid files go to `errors`, not the whole call.
#[tauri::command]
pub async fn list_analyses(app: tauri::AppHandle) -> Result<AnalysisListing, String> {
    let dir = dir_path(&app)?;
    // Reading every file is blocking I/O: keep it off the async runtime's worker threads.
    tauri::async_runtime::spawn_blocking(move || list_dir(dir))
        .await
        .map_err(|e| format!("listing the analyses failed: {e}"))?
}

fn list_dir(dir: PathBuf) -> Result<AnalysisListing, String> {
    let mut out = AnalysisListing { items: vec![], errors: vec![] };
    let rd = match fs::read_dir(&dir) {
        Ok(rd) => rd,
        Err(e) if e.kind() == io::ErrorKind::NotFound => return Ok(out), // nothing saved yet
        Err(e) => return Err(io_msg("cannot read the folder", &dir, &e)),
    };
    for ent in rd.flatten() {
        let path = ent.path();
        let Some(name) = path.file_name().and_then(|n| n.to_str()).map(str::to_string) else {
            continue;
        };
        if name.starts_with('.') || !name.ends_with(".json") || !path.is_file() {
            continue;
        }
        let stem = name.trim_end_matches(".json").to_string();
        let res = if !valid_id(&stem) {
            Err("the file name is not a valid analysis id".to_string())
        } else {
            fs::read_to_string(&path)
                .map_err(|e| io_msg("cannot read", &path, &e))
                .and_then(|t| entry_from(&stem, &name, &t))
        };
        match res {
            Ok(e) => out.items.push(e),
            Err(error) => out.errors.push(AnalysisFileError { file: name, error }),
        }
    }
    out.items.sort_by(|a, b| b.created_at.cmp(&a.created_at));
    out.errors.sort_by(|a, b| a.file.cmp(&b.file));
    Ok(out)
}

/// The raw JSON text of one analysis.
#[tauri::command]
pub async fn read_analysis(app: tauri::AppHandle, id: String) -> Result<String, String> {
    let path = file_path(&app, &id)?;
    fs::read_to_string(&path).map_err(|e| io_msg("cannot read", &path, &e))
}

/// Delete one analysis file; false when it did not exist.
#[tauri::command]
pub async fn delete_analysis(app: tauri::AppHandle, id: String) -> Result<bool, String> {
    let path = file_path(&app, &id)?;
    match fs::remove_file(&path) {
        Ok(()) => Ok(true),
        Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(false),
        Err(e) => Err(io_msg("cannot delete", &path, &e)),
    }
}
