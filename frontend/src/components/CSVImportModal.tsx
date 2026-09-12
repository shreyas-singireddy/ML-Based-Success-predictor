import React, { useState } from 'react';
import { CSVValidationPreview, CSVImportResult } from '../types';
import { Modal } from './ui/Modal';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Alert } from './ui/Alert';
import { Select } from './ui/Select';
import { csvApi } from '../services/api';
import { Upload, FileText, CheckCircle2, AlertOctagon, Download, ArrowRight, RefreshCw } from 'lucide-react';

interface CSVImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

export const CSVImportModal: React.FC<CSVImportModalProps> = ({
  isOpen,
  onClose,
  onImportComplete
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<CSVValidationPreview | null>(null);
  const [importResult, setImportResult] = useState<CSVImportResult | null>(null);
  const [duplicatePolicy, setDuplicatePolicy] = useState('SKIP_EXISTING');
  const [error, setError] = useState<string | null>(null);

  const resetState = () => {
    setFile(null);
    setPreview(null);
    setImportResult(null);
    setError(null);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUploadAndValidate = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const previewData = await csvApi.validateCsv(file);
      setPreview(previewData);
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'CSV validation failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!preview) return;
    setLoading(true);
    setError(null);

    try {
      const result = await csvApi.confirmImport(preview.import_batch_token, duplicatePolicy);
      setImportResult(result);
      onImportComplete();
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Import commit failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadSample = () => {
    const sampleHeaders = 'student_id,name,gender,age,department,semester,academic_year,attendance,previous_cgpa,mid_1,mid_2,internal_marks,backlogs,semester_cgpa,grade,historical_risk_level\n';
    const sampleRow1 = 'STU-SAMPLE-001,John Smith,MALE,20,CS,1,2024-2025,88.5,8.0,82.0,85.0,83.5,0,8.4,A,LOW\n';
    const sampleRow2 = 'STU-SAMPLE-002,Sarah Connor,FEMALE,21,IT,1,2024-2025,92.0,8.6,90.0,91.0,90.5,0,8.9,A+,LOW\n';
    const blob = new Blob([sampleHeaders + sampleRow1 + sampleRow2], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_students_import_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Bulk Import Student Records via CSV"
      maxWidth="880px"
    >
      {error && <Alert variant="error">{error}</Alert>}

      {/* STEP 1: Upload & Validate Screen */}
      {!preview && !importResult && (
        <div>
          <div
            style={{
              border: '2px dashed var(--border-glass)',
              borderRadius: 'var(--radius-lg)',
              padding: '2.5rem',
              textAlign: 'center',
              background: 'rgba(15, 23, 42, 0.4)',
              cursor: 'pointer',
              marginBottom: '1.5rem',
              transition: 'all var(--transition-fast)'
            }}
            onClick={() => document.getElementById('csvFileInput')?.click()}
          >
            <Upload size={36} color="var(--color-primary)" style={{ margin: '0 auto 0.75rem auto' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.3rem' }}>
              {file ? file.name : 'Choose CSV File or Drag & Drop'}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Supports standard formatted CSV files up to 10MB
            </p>
            <input
              id="csvFileInput"
              type="file"
              accept=".csv"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button
              variant="outline"
              size="sm"
              icon={<Download size={16} />}
              onClick={handleDownloadSample}
            >
              Download Sample CSV Template
            </Button>
            <Button
              disabled={!file}
              loading={loading}
              icon={<ArrowRight size={16} />}
              onClick={handleUploadAndValidate}
            >
              Upload & Validate Preview
            </Button>
          </div>
        </div>
      )}

      {/* STEP 2: Validation & Preview Screen */}
      {preview && !importResult && (
        <div>
          {/* Summary Badges */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <div className="glass-card" style={{ padding: '0.85rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Rows</span>
              <p style={{ fontSize: '1.3rem', fontWeight: 800 }}>{preview.total_rows}</p>
            </div>
            <div className="glass-card" style={{ padding: '0.85rem', borderColor: 'rgba(16, 185, 129, 0.4)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-success)', textTransform: 'uppercase' }}>Valid Rows</span>
              <p style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-success)' }}>{preview.valid_rows_count}</p>
            </div>
            <div className="glass-card" style={{ padding: '0.85rem', borderColor: preview.invalid_rows_count > 0 ? 'rgba(244, 63, 94, 0.4)' : 'var(--border-subtle)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-danger)', textTransform: 'uppercase' }}>Invalid Rows</span>
              <p style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-danger)' }}>{preview.invalid_rows_count}</p>
            </div>
            <div className="glass-card" style={{ padding: '0.85rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-warning)', textTransform: 'uppercase' }}>Duplicate Rows</span>
              <p style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-warning)' }}>{preview.duplicate_in_file_count}</p>
            </div>
          </div>

          {/* Conflict Policy Selector */}
          <div className="glass-card" style={{ padding: '1rem', marginBottom: '1.25rem' }}>
            <Select
              label="Conflict & Existing Student Policy"
              options={[
                { value: 'SKIP_EXISTING', label: 'Skip Existing — Do not overwrite existing terms' },
                { value: 'UPDATE_EXISTING', label: 'Update Existing — Update student profile & semester values' },
                { value: 'FAIL_ON_CONFLICT', label: 'Strict Rollback — Cancel entire import if any record exists' }
              ]}
              value={duplicatePolicy}
              onChange={(e) => setDuplicatePolicy(e.target.value)}
            />
          </div>

          {/* Row-Level Errors Inspector */}
          {preview.errors.length > 0 && (
            <div style={{ marginBottom: '1.25rem' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-danger)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <AlertOctagon size={18} /> Detected Validation Errors ({preview.errors.length})
              </h4>
              <div style={{ maxHeight: '180px', overflowY: 'auto', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: 'var(--radius-md)' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Line</th>
                      <th>Student ID</th>
                      <th>Column</th>
                      <th>Validation Issue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.errors.map((err, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 700, color: 'var(--color-danger)' }}>Row {err.row_number}</td>
                        <td>{err.student_id || '-'}</td>
                        <td><Badge variant="neutral">{err.field}</Badge></td>
                        <td style={{ color: 'var(--text-primary)' }}>{err.error_message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Preview Rows Table */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.5rem' }}>Preview Validated Rows</h4>
            <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Dept</th>
                    <th>Sem</th>
                    <th>Attendance</th>
                    <th>SGPA</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.preview_items.map((row) => (
                    <tr key={row.row_number}>
                      <td>
                        {row.is_valid ? (
                          <Badge variant="success">Valid</Badge>
                        ) : (
                          <Badge variant="danger">Invalid</Badge>
                        )}
                      </td>
                      <td>{row.student_id}</td>
                      <td>{row.name}</td>
                      <td>{row.department_code}</td>
                      <td>Sem {row.semester}</td>
                      <td>{row.attendance}%</td>
                      <td>{row.semester_cgpa ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button variant="outline" size="sm" icon={<RefreshCw size={16} />} onClick={resetState}>
              Upload Different File
            </Button>
            <Button
              disabled={preview.valid_rows_count === 0}
              loading={loading}
              icon={<CheckCircle2 size={18} />}
              onClick={handleConfirmImport}
            >
              Confirm & Import {preview.valid_rows_count} Records
            </Button>
          </div>
        </div>
      )}

      {/* STEP 3: Final Import Result Screen */}
      {importResult && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <CheckCircle2 size={48} color="var(--color-success)" style={{ margin: '0 auto 1rem auto' }} />
          <h3 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
            Import Completed Successfully!
          </h3>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            {importResult.message}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', maxWidth: '500px', margin: '0 auto 2rem auto' }}>
            <div className="glass-card" style={{ padding: '0.85rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>New Students</span>
              <p style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--color-primary)' }}>{importResult.created_students}</p>
            </div>
            <div className="glass-card" style={{ padding: '0.85rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Term Records</span>
              <p style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--color-success)' }}>{importResult.created_academic_records}</p>
            </div>
            <div className="glass-card" style={{ padding: '0.85rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Skipped/Updated</span>
              <p style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-warning)' }}>{importResult.skipped_records + importResult.updated_students}</p>
            </div>
          </div>

          <Button onClick={handleClose}>Done</Button>
        </div>
      )}
    </Modal>
  );
};
