import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Student, Department } from '../types';
import { studentApi, departmentApi } from '../services/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Badge } from '../components/ui/Badge';
import { Tabs } from '../components/ui/Tabs';
import { Pagination } from '../components/ui/Pagination';
import { Alert } from '../components/ui/Alert';
import { StudentProfileModal } from '../components/StudentProfileModal';
import { StudentFormModal } from '../components/StudentFormModal';
import { CSVImportModal } from '../components/CSVImportModal';
import {
  GraduationCap,
  LogOut,
  Search,
  Plus,
  Upload,
  Eye,
  Edit2,
  Archive,
  RefreshCcw,
  Users,
  Shield,
  Layers
} from 'lucide-react';

export const StudentManagementPage: React.FC = () => {
  const { user, logout } = useAuth();

  const [students, setStudents] = useState<Student[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const limit = 10;

  // Filters
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedSem, setSelectedSem] = useState('');
  const [activeTab, setActiveTab] = useState('active'); // 'active' | 'archived'

  // Modals
  const [selectedStudentForView, setSelectedStudentForView] = useState<Student | null>(null);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [selectedStudentForEdit, setSelectedStudentForEdit] = useState<Student | null>(null);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch departments on mount
  useEffect(() => {
    departmentApi.getDepartments().then(setDepartments).catch(() => {});
  }, []);

  // Fetch students
  const fetchStudents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await studentApi.getStudents({
        search: search.trim() || undefined,
        department_id: selectedDept || undefined,
        semester: selectedSem ? parseInt(selectedSem, 10) : undefined,
        is_archived: activeTab === 'archived',
        page,
        limit
      });
      setStudents(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to fetch students';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [page, activeTab, selectedDept, selectedSem]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchStudents();
  };

  const handleOpenProfile = async (student: Student) => {
    try {
      const full = await studentApi.getStudentById(student.id);
      setSelectedStudentForView(full);
      setIsProfileModalOpen(true);
    } catch {
      setSelectedStudentForView(student);
      setIsProfileModalOpen(true);
    }
  };

  const handleArchive = async (student: Student) => {
    if (window.confirm(`Are you sure you want to archive student ${student.name} (${student.student_number})?`)) {
      try {
        await studentApi.archiveStudent(student.id);
        fetchStudents();
      } catch (err: any) {
        alert(err.response?.data?.error?.message || 'Archive failed');
      }
    }
  };

  const handleRestore = async (student: Student) => {
    try {
      await studentApi.restoreStudent(student.id);
      fetchStudents();
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Restore failed');
    }
  };

  const deptOptions = [
    { value: '', label: 'All Departments' },
    ...departments.map((d) => ({ value: d.id, label: `${d.code} — ${d.name}` }))
  ];

  const semOptions = [
    { value: '', label: 'All Semesters' },
    ...Array.from({ length: 8 }, (_, i) => ({ value: (i + 1).toString(), label: `Semester ${i + 1}` }))
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header
        className="glass-panel"
        style={{
          borderRadius: 0,
          borderLeft: 'none',
          borderRight: 'none',
          borderTop: 'none',
          padding: '0.85rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 40
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--color-primary), #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <GraduationCap size={22} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Student Success Predictor
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Academic Data Management
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{ textAlign: 'right' }}>
            <p style={{ fontSize: '0.9rem', fontWeight: 700 }}>{user?.full_name}</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
              <Badge variant={user?.role === 'ADMIN' ? 'danger' : 'info'}>
                {user?.role}
              </Badge>
            </div>
          </div>
          <Button variant="outline" size="sm" icon={<LogOut size={16} />} onClick={logout}>
            Sign Out
          </Button>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ maxWidth: '1280px', width: '100%', margin: '0 auto', padding: '2rem 1.5rem', flex: 1 }}>
        {/* Page Header with Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Student Management Cockpit
            </h1>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Add, inspect, edit, and bulk-import validated longitudinal academic records
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Button
              variant="outline"
              icon={<Upload size={16} />}
              onClick={() => setIsCsvModalOpen(true)}
            >
              Bulk Import CSV
            </Button>
            <Button
              icon={<Plus size={16} />}
              onClick={() => {
                setSelectedStudentForEdit(null);
                setIsFormModalOpen(true);
              }}
            >
              Add Student
            </Button>
          </div>
        </div>

        {error && <Alert variant="error">{error}</Alert>}

        {/* Filter and Search Bar */}
        <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
          <form onSubmit={handleSearchSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', alignItems: 'flex-end' }}>
            <Input
              label="Search Students"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by ID (e.g. STU-2023) or Name..."
            />
            <Select
              label="Department"
              options={deptOptions}
              value={selectedDept}
              onChange={(e) => {
                setSelectedDept(e.target.value);
                setPage(1);
              }}
            />
            <Select
              label="Semester"
              options={semOptions}
              value={selectedSem}
              onChange={(e) => {
                setSelectedSem(e.target.value);
                setPage(1);
              }}
            />
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <Button type="submit" icon={<Search size={16} />} style={{ flex: 1 }}>
                Search
              </Button>
              <Button
                type="button"
                variant="outline"
                icon={<RefreshCcw size={16} />}
                onClick={() => {
                  setSearch('');
                  setSelectedDept('');
                  setSelectedSem('');
                  setPage(1);
                  fetchStudents();
                }}
              />
            </div>
          </form>
        </div>

        {/* Status Tabs: Active vs. Archived */}
        <Tabs
          tabs={[
            { id: 'active', label: 'Active Students', count: activeTab === 'active' ? total : undefined },
            { id: 'archived', label: 'Archived Roster', count: activeTab === 'archived' ? total : undefined }
          ]}
          activeTab={activeTab}
          onChange={(tab) => {
            setActiveTab(tab);
            setPage(1);
          }}
        />

        {/* Student Table */}
        <div className="table-container glass-panel">
          <table className="data-table">
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Name</th>
                <th>Gender / Age</th>
                <th>Department</th>
                <th>Current Sem</th>
                <th>Actual CGPA</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    Loading student data...
                  </td>
                </tr>
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No students match the current filters.
                  </td>
                </tr>
              ) : (
                students.map((student) => (
                  <tr key={student.id}>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--color-primary)' }}>
                        {student.student_number}
                      </span>
                    </td>
                    <td>
                      <strong style={{ color: 'var(--text-primary)' }}>{student.name}</strong>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {student.gender} • {student.age} yrs
                      </span>
                    </td>
                    <td>
                      <Badge variant="neutral">
                        {student.department_code || 'N/A'}
                      </Badge>
                    </td>
                    <td>Semester {student.current_semester}</td>
                    <td>
                      <span
                        style={{
                          fontWeight: 800,
                          fontSize: '1rem',
                          color: (student.cumulative_gpa || 0) >= 8.0
                            ? 'var(--color-success)'
                            : (student.cumulative_gpa || 0) >= 6.5
                            ? 'var(--color-warning)'
                            : 'var(--color-danger)'
                        }}
                      >
                        {student.cumulative_gpa !== undefined && student.cumulative_gpa !== null
                          ? Number(student.cumulative_gpa).toFixed(2)
                          : '—'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem' }}>
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={<Eye size={14} />}
                          onClick={() => handleOpenProfile(student)}
                        >
                          Profile
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          icon={<Edit2 size={14} />}
                          onClick={() => {
                            setSelectedStudentForEdit(student);
                            setIsFormModalOpen(true);
                          }}
                        />
                        {activeTab === 'active' ? (
                          <Button
                            variant="danger"
                            size="sm"
                            icon={<Archive size={14} />}
                            onClick={() => handleArchive(student)}
                          />
                        ) : (
                          <Button
                            variant="primary"
                            size="sm"
                            icon={<RefreshCcw size={14} />}
                            onClick={() => handleRestore(student)}
                          >
                            Restore
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <Pagination
          page={page}
          pages={pages}
          total={total}
          limit={limit}
          onPageChange={(p) => setPage(p)}
        />
      </main>

      {/* Modals */}
      <StudentProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        student={selectedStudentForView}
        onRecordAdded={() => {
          if (selectedStudentForView) handleOpenProfile(selectedStudentForView);
          fetchStudents();
        }}
      />

      <StudentFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        studentToEdit={selectedStudentForEdit}
        departments={departments}
        onSuccess={() => fetchStudents()}
      />

      <CSVImportModal
        isOpen={isCsvModalOpen}
        onClose={() => setIsCsvModalOpen(false)}
        onImportComplete={() => fetchStudents()}
      />
    </div>
  );
};
