-- Script de primera ejecución para Azure SQL Database
-- Ejecutar conectado directamente a la base HistoriasClinicas

-- Tabla: Usuarios
CREATE TABLE Usuarios (
    IdUsuario INT IDENTITY(1,1) PRIMARY KEY,
    NombreUsuario VARCHAR(100) NOT NULL UNIQUE,
    HashContrasena VARCHAR(255) NOT NULL,
    NombreCompleto VARCHAR(150) NOT NULL,
    CorreoElectronico VARCHAR(150) NULL,
    Rol VARCHAR(20) NOT NULL CHECK (Rol IN ('admin', 'admission')),
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME NOT NULL DEFAULT GETDATE()
);
GO

-- Tabla: Especialidades
CREATE TABLE Especialidades (
    IdEspecialidad INT IDENTITY(1,1) PRIMARY KEY,
    NombreEspecialidad VARCHAR(100) NOT NULL,
    Descripcion VARCHAR(255) NULL
);
GO

-- Tabla: Medicos
CREATE TABLE Medicos (
    IdMedico INT IDENTITY(1,1) PRIMARY KEY,
    NombreMedico VARCHAR(100) NOT NULL,
    IdEspecialidad INT NOT NULL,
    CONSTRAINT FK_Medicos_Especialidades
        FOREIGN KEY (IdEspecialidad) REFERENCES Especialidades(IdEspecialidad)
);
GO

-- Tabla: ResponsablesTriaje
CREATE TABLE ResponsablesTriaje (
    IdResponsableTriaje INT IDENTITY(1,1) PRIMARY KEY,
    NombreResponsable VARCHAR(100) NOT NULL,
    Area VARCHAR(100) NULL
);
GO

-- Tabla: Historias
CREATE TABLE Historias (
    IdHistoria INT IDENTITY(1,1) PRIMARY KEY,
    NumeroHistoria VARCHAR(50) NOT NULL,
    IdMedico INT NOT NULL,
    Turno VARCHAR(10) NOT NULL CHECK (Turno IN ('M', 'T')),
    IdResponsableTriaje INT NOT NULL,
    Estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente'
        CHECK (Estado IN ('Pendiente', 'Recibido')),
    IdUsuarioRegistro INT NOT NULL,
    FechaRegistro DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Historias_Medicos
        FOREIGN KEY (IdMedico) REFERENCES Medicos(IdMedico),
    CONSTRAINT FK_Historias_ResponsablesTriaje
        FOREIGN KEY (IdResponsableTriaje) REFERENCES ResponsablesTriaje(IdResponsableTriaje),
    CONSTRAINT FK_Historias_Usuarios
        FOREIGN KEY (IdUsuarioRegistro) REFERENCES Usuarios(IdUsuario)
);
GO

-- Tabla: Pacientes
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
GO

CREATE INDEX IX_Pacientes_NumeroHistoriaClinica ON Pacientes (NumeroHistoriaClinica);
GO

CREATE INDEX IX_Pacientes_DNI ON Pacientes (DNI) WHERE DNI IS NOT NULL;
GO

CREATE INDEX IX_Pacientes_NombreCompleto ON Pacientes (NombreCompleto);
GO

-- Tabla: TokensRegistro
CREATE TABLE TokensRegistro (
    IdTokenRegistro INT IDENTITY(1,1) PRIMARY KEY,
    Token VARCHAR(100) NOT NULL UNIQUE,
    FechaExpiracion DATETIME NOT NULL,
    Usado BIT NOT NULL DEFAULT 0,
    FechaCreacion DATETIME NOT NULL DEFAULT GETDATE()
);
GO

-- Tabla: MetricasContrasena
CREATE TABLE MetricasContrasena (
    IdMetricaContrasena INT IDENTITY(1,1) PRIMARY KEY,
    IdUsuario INT NOT NULL,
    LongitudContrasena INT NOT NULL,
    TiempoGeneracionMs INT NOT NULL,
    NivelFortaleza VARCHAR(20) NOT NULL,
    FechaCreacion DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_MetricasContrasena_Usuarios
        FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario)
);
GO

-- Tabla: TokensRecuperacionContrasena
CREATE TABLE TokensRecuperacionContrasena (
    IdTokenRecuperacion INT IDENTITY(1,1) PRIMARY KEY,
    IdUsuario INT NOT NULL,
    Token VARCHAR(120) NOT NULL UNIQUE,
    FechaExpiracion DATETIME NOT NULL,
    Usado BIT NOT NULL DEFAULT 0,
    FechaCreacion DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_TokensRecuperacionContrasena_Usuarios
        FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario)
);
GO

-- Usuario administrador por defecto (password: admin123)
IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE NombreUsuario = 'admin')
BEGIN
    INSERT INTO Usuarios (
        NombreUsuario,
        HashContrasena,
        NombreCompleto,
        CorreoElectronico,
        Rol,
        Activo,
        FechaCreacion
    )
    VALUES (
        'admin',
        '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
        'Administrador Principal',
        NULL,
        'admin',
        1,
        GETDATE()
    );
END
GO
