# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('.env', '.'),  # Include the .env file if you have one
    ],
    hiddenimports=[
        'flask',
        'werkzeug',
        'sqlalchemy',
        'flask_sqlalchemy',
        'flask_login',
        'dotenv', 
        'models',
        'routes',
        'utils',
        'backup_utils',
        'pandas',
        'openpyxl',
        'reportlab',
        'psycopg2',
        'email_validator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SalesTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='generated-icon.png',  # Use the icon from your workspace
) 