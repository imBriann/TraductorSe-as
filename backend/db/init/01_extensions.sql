-- ============================================================================
--  Inicialización de PostgreSQL para LSC i5.0
--  Las tablas las crea SQLAlchemy en el arranque (init_models()).
--  Aquí solo habilitamos extensiones útiles e índices auxiliares.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Búsqueda por texto en traducciones (se aplica si la tabla existe)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'translations') THEN
        CREATE INDEX IF NOT EXISTS idx_translations_text_trgm
            ON translations USING gin (natural_text gin_trgm_ops);
    END IF;
END$$;
