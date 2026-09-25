CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    es_admin INTEGER NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1,
    creado TEXT NOT NULL DEFAULT (datetime('now'))
);

-- El NHC nunca se guarda en claro: se cifra (para poder mostrarlo a usuarios
-- autenticados) y se guarda un HMAC (para detectar duplicados y buscar).
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE,
    nhc_hmac TEXT NOT NULL UNIQUE,
    nhc_cifrado TEXT NOT NULL,
    sexo TEXT,
    creado TEXT NOT NULL DEFAULT (datetime('now')),
    creado_por INTEGER REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS procedimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
    cirujano_id INTEGER NOT NULL REFERENCES usuarios(id),
    tipo TEXT NOT NULL,
    fecha_cirugia TEXT NOT NULL,
    datos TEXT NOT NULL DEFAULT '{}',
    creado TEXT NOT NULL DEFAULT (datetime('now')),
    creado_por INTEGER REFERENCES usuarios(id),
    modificado TEXT,
    modificado_por INTEGER REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS seguimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedimiento_id INTEGER NOT NULL REFERENCES procedimientos(id) ON DELETE CASCADE,
    hito TEXT NOT NULL,
    dias INTEGER NOT NULL,
    fecha_prevista TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',   -- pendiente | completado | no_realizable
    datos TEXT NOT NULL DEFAULT '{}',
    motivo_no_realizable TEXT,
    completado TEXT,
    completado_por INTEGER REFERENCES usuarios(id),
    recordatorios_enviados INTEGER NOT NULL DEFAULT 0,
    ultimo_recordatorio TEXT,
    UNIQUE (procedimiento_id, hito)
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_id INTEGER,
    accion TEXT NOT NULL,
    entidad TEXT,
    entidad_id INTEGER,
    detalle TEXT
);

CREATE INDEX IF NOT EXISTS idx_seg_pendientes ON seguimientos (estado, fecha_prevista);
CREATE INDEX IF NOT EXISTS idx_proc_paciente ON procedimientos (paciente_id);
