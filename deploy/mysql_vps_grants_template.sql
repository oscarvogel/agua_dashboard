-- Template de permisos MySQL para el VPS del dashboard.
-- Revisar host, contrasenas y nombre de base antes de ejecutar.
-- Este archivo NO debe contener credenciales reales versionadas.

CREATE DATABASE IF NOT EXISTS `agua_dashboard`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Usuario usado solo por el agente de sincronizacion instalado en la cooperativa.
-- Cambiar '%' por la IP publica fija de la cooperativa si esta disponible.
CREATE USER IF NOT EXISTS 'sync_writer'@'%' IDENTIFIED BY 'CAMBIAR_PASSWORD_SYNC';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES, TRIGGER
ON `agua_dashboard`.*
TO 'sync_writer'@'%';

-- Usuario usado por Django/dashboard. Debe ser solo lectura.
CREATE USER IF NOT EXISTS 'dashboard_reader'@'%' IDENTIFIED BY 'CAMBIAR_PASSWORD_READER';

GRANT SELECT
ON `agua_dashboard`.*
TO 'dashboard_reader'@'%';

FLUSH PRIVILEGES;

-- Chequeos sugeridos despues de ejecutar:
-- SHOW GRANTS FOR 'sync_writer'@'%';
-- SHOW GRANTS FOR 'dashboard_reader'@'%';
