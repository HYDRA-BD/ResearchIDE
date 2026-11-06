# PHASE 1 — APPLICATION FOUNDATION

Implement the desktop application foundation using Python and PySide6.

Follow the approved Phase 0 architecture. Do not redesign the architecture unnecessarily.

## 1. Main application

Build a professional Windows desktop application with:

- Main window.
- Application menu.
- Adaptive hybrid interface.
- Navigation sidebar.
- Main workspace.
- Status bar.
- Notifications.
- Dialog system.

The application should look like a professional academic productivity suite.

Use a consistent design system.

## 2. Main workspace

Implement:

- Home dashboard.
- Recent projects.
- Recent documents.
- Project explorer.
- New project action.
- Open project action.
- New document action.
- Settings.

## 3. Project management

Users must be able to:

- Create projects.
- Rename projects.
- Open projects.
- Close projects.
- Delete projects with confirmation.
- Organize project folders.
- Create manuscripts.
- Store project notes.
- Store research PDFs.
- Organize figures and references.

## 4. Database

Implement the approved SQLite database design.

Requirements:
- Database initialization.
- Schema migrations.
- Data access layer.
- Transaction handling.
- Error recovery.
- Integrity checks.

Do not place SQL queries throughout the UI code.

## 5. Settings

Implement settings for:

- Application appearance.
- Default project directory.
- Autosave configuration.
- Local AI configuration.
- LaTeX compiler configuration.
- PDF preview settings.
- Performance settings.

## 6. File management

Implement safe local file operations.

Do not allow accidental overwriting without confirmation.

Use appropriate file validation.

## 7. Testing

Test:

- Application startup.
- Project creation.
- Project reopening.
- Project deletion.
- Database persistence.
- Settings persistence.
- Error handling.

## 8. Completion

The application must launch successfully as a functional desktop application.

Do not proceed to Phase 2 until the Phase 1 implementation and tests are complete.