"""Submission Preparation & Publication Compliance Dialog for ResearchIDE."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QFileDialog,
    QMessageBox,
)
from src.services.template_service import PUBLISHER_TEMPLATES, TemplateMigrator
from src.services.compliance_auditor import PublicationComplianceAuditor, ComplianceReport
from src.services.submission_bundler import SubmissionBundler
from src.storage.file_manager import FileManager
from src.utils.logger import app_logger


class SubmissionDialog(QDialog):
    """Dialog for selecting publication templates, running compliance audits, and exporting submission bundles."""

    def __init__(
        self,
        project_dir: Path,
        current_tex_file: Path,
        parent: Optional[QDialog] = None,
    ) -> None:
        super().__init__(parent)
        self.project_dir = Path(project_dir).resolve()
        self.current_tex_file = Path(current_tex_file).resolve()
        self.last_report: Optional[ComplianceReport] = None

        self.setWindowTitle("Publication Preparation & Submission Packager")
        self.resize(680, 560)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Target Publisher Profile Selector
        tpl_group = QGroupBox("Target Publisher & Template Profile")
        t_layout = QVBoxLayout(tpl_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Target Profile:"))
        self.template_combo = QComboBox(self)
        for key, tpl in PUBLISHER_TEMPLATES.items():
            self.template_combo.addItem(f"{tpl.publisher}: {tpl.name}", key)
        row1.addWidget(self.template_combo, 1)

        btn_apply_template = QPushButton("🔄 Apply Template to File", self)
        btn_apply_template.clicked.connect(self.action_apply_template)
        row1.addWidget(btn_apply_template)
        t_layout.addLayout(row1)

        self.template_desc_label = QLabel(self)
        self.template_desc_label.setStyleSheet("color: #777; font-size: 11px;")
        t_layout.addWidget(self.template_desc_label)
        self.template_combo.currentIndexChanged.connect(self._update_template_desc)
        self._update_template_desc()

        layout.addWidget(tpl_group)

        # 2. Compliance Audit Section
        audit_group = QGroupBox("Automated Compliance Audit")
        a_layout = QVBoxLayout(audit_group)

        a_btn_row = QHBoxLayout()
        btn_run_audit = QPushButton("🔍 Run Compliance Audit", self)
        btn_run_audit.setStyleSheet("font-weight: bold; background-color: #1a73e8; color: white;")
        btn_run_audit.clicked.connect(self.action_run_audit)
        a_btn_row.addWidget(btn_run_audit)
        a_btn_row.addStretch()
        a_layout.addLayout(a_btn_row)

        self.audit_report_edit = QTextEdit(self)
        self.audit_report_edit.setReadOnly(True)
        self.audit_report_edit.setPlaceholderText("Click 'Run Compliance Audit' to evaluate manuscript formatting...")
        a_layout.addWidget(self.audit_report_edit)

        layout.addWidget(audit_group)

        # 3. Submission Package Export Actions
        action_layout = QHBoxLayout()
        btn_export_zip = QPushButton("📦 Export Complete Submission Bundle (.zip)...", self)
        btn_export_zip.setStyleSheet("font-weight: bold; padding: 6px 12px;")
        btn_export_zip.clicked.connect(self.action_export_zip)

        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.accept)

        action_layout.addWidget(btn_export_zip)
        action_layout.addStretch()
        action_layout.addWidget(btn_close)
        layout.addLayout(action_layout)

    def _update_template_desc(self) -> None:
        key = self.template_combo.currentData()
        tpl = PUBLISHER_TEMPLATES.get(key)
        if tpl:
            self.template_desc_label.setText(
                f"{tpl.description} (Abstract Limit: {tpl.abstract_word_limit} words, Style: {tpl.bibstyle})"
            )

    def action_apply_template(self) -> None:
        """Switch manuscript to the selected template without destroying content."""
        key = self.template_combo.currentData()
        tpl = PUBLISHER_TEMPLATES.get(key)
        if not tpl:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Template Switch",
            f"Apply '{tpl.name}' documentclass and packages to '{self.current_tex_file.name}'?\n"
            "All sections, equations, citations, figures, and macros will be safely preserved.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                content = FileManager.read_text(self.current_tex_file)
                updated = TemplateMigrator.apply_template(content, key)
                FileManager.atomic_write(self.current_tex_file, updated)
                QMessageBox.information(
                    self, "Template Applied", f"Successfully migrated to '{tpl.name}' format."
                )
                self.action_run_audit()
            except Exception as e:
                QMessageBox.critical(self, "Migration Error", f"Failed applying template: {e}")

    def action_run_audit(self) -> None:
        """Run compliance verification against target publisher."""
        key = self.template_combo.currentData()
        try:
            tex_content = FileManager.read_text(self.current_tex_file)
            # Find references.bib if exists
            bib_content = ""
            bib_files = list(self.project_dir.glob("**/*.bib"))
            if bib_files:
                bib_content = FileManager.read_text(bib_files[0])

            self.last_report = PublicationComplianceAuditor.audit_manuscript(
                tex_content,
                template_key=key,
                bib_source=bib_content,
            )

            lines = [
                f"=== COMPLIANCE REPORT: {self.last_report.template_name.upper()} ===",
                f"Overall Status: {'✅ COMPLIANT' if self.last_report.is_compliant else '❌ ISSUES DETECTED'}",
                f"Estimated Words: ~{self.last_report.estimated_word_count} | Abstract: {self.last_report.abstract_word_count} words",
                "",
                "--- PASSED VERIFICATIONS ---",
            ]
            for p in self.last_report.passed_checks:
                lines.append(f"  ✓ {p}")

            if self.last_report.failed_checks:
                lines.append("\n--- FAILED / ACTION REQUIRED ---")
                for f in self.last_report.failed_checks:
                    lines.append(f"  ✗ {f}")

            if self.last_report.warnings:
                lines.append("\n--- WARNINGS ---")
                for w in self.last_report.warnings:
                    lines.append(f"  ⚠ {w}")

            lines.append("\n--- MANDATORY MANUAL CHECKS ---")
            for m in self.last_report.manual_verifications:
                lines.append(f"  • {m}")

            self.audit_report_edit.setPlainText("\n".join(lines))

        except Exception as e:
            QMessageBox.critical(self, "Audit Error", f"Failed auditing manuscript: {e}")

    def action_export_zip(self) -> None:
        """Package all submission assets into a ZIP file."""
        if not self.last_report:
            self.action_run_audit()

        default_zip = self.project_dir / f"submission_{self.project_dir.name}.zip"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Submission Package", str(default_zip), "ZIP Archives (*.zip)"
        )
        if not file_path:
            return

        pdf_candidate = self.current_tex_file.with_suffix(".pdf")
        pdf_file = pdf_candidate if pdf_candidate.exists() else None

        try:
            zip_path = SubmissionBundler.create_submission_package(
                project_dir=self.project_dir,
                main_tex_file=self.current_tex_file,
                compiled_pdf_file=pdf_file,
                output_zip_path=Path(file_path),
                compliance_report=self.last_report,
            )
            QMessageBox.information(
                self,
                "Submission Package Created",
                f"Submission bundle exported successfully to:\n{zip_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Packaging Error", f"Failed creating submission bundle: {e}")
