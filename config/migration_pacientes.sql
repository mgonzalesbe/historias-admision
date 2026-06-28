-- Migración: tabla Pacientes (ejecutar en Azure SQL / SQL Server existente)
-- Conectado a la base HistoriasClinicas (free-sql-db-0676007 o equivalente)

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Pacientes')
BEGIN
    CREATE TABLE Pacientes (
        IdPaciente INT IDENTITY(1,1) PRIMARY KEY,
        NumeroHistoriaClinica VARCHAR(50) NOT NULL,
        DNI VARCHAR(20) NULL,
        NombreCompleto VARCHAR(200) NOT NULL,
        FechaNacimiento DATE NULL,
        Direccion VARCHAR(255) NULL,
        NombrePadre VARCHAR(150) NULL,
        NombreMadre VARCHAR(150) NULL,
        FechaCreacion DATETIME NOT NULL DEFAULT GETDATE(),
        Activo BIT NOT NULL DEFAULT 1
    );
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_Pacientes_NumeroHistoriaClinica' AND object_id = OBJECT_ID('Pacientes')
)
BEGIN
    CREATE INDEX IX_Pacientes_NumeroHistoriaClinica
        ON Pacientes (NumeroHistoriaClinica);
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_Pacientes_DNI' AND object_id = OBJECT_ID('Pacientes')
)
BEGIN
    CREATE INDEX IX_Pacientes_DNI ON Pacientes (DNI) WHERE DNI IS NOT NULL;
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_Pacientes_NombreCompleto' AND object_id = OBJECT_ID('Pacientes')
)
BEGIN
    CREATE INDEX IX_Pacientes_NombreCompleto ON Pacientes (NombreCompleto);
END
GO
