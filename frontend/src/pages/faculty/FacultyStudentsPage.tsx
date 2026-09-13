import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search,
  Filter,
  Users,
  AlertTriangle,
  ArrowUpDown,
  TrendingDown,
  TrendingUp,
  Minus,
  ChevronRight,
  RefreshCw,
  SlidersHorizontal,
  GraduationCap,
} from 'lucide-react';
import { facultyApi } from '../../services/facultyApi';
import { FacultyStudentListResponse, FacultyStudentSummary } from '../../types/faculty';

export const FacultyStudentsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [data, setData] = useState<FacultyStudentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [riskLevel, setRiskLevel] = useState(searchParams.get('risk_level') || 'ALL');
  const [semester, setSemester] = useState(searchParams.get('semester') || '');
  const [minAttendance, setMinAttendance] = useState(searchParams.get('min_attendance') || '');
  const [maxAttendance, setMaxAttendance] = useState(searchParams.get('max_attendance') || '');
  const [hasBacklogs, setHasBacklogs] = useState(searchParams.get('has_backlogs') || '');
  const [sortBy, setSortBy] = useState(searchParams.get('sort_by') || 'priority');
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10));
  const limit = 15;

  const fetchStudents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await facultyApi.getStudents({
        search: search.trim() || undefined,
        risk_level: riskLevel !== 'ALL' ? riskLevel : undefined,
        semester: semester ? parseInt(semester, 10) : undefined,
        min_attendance: minAttendance ? parseFloat(minAttendance) : undefined,
        max_attendance: maxAttendance ? parseFloat(maxAttendance) : undefined,
        has_backlogs: hasBacklogs === 'yes' ? true : hasBacklogs === 'no' ? false : undefined,
        sort_by: sortBy,
        page,
        limit,
      });
      setData(res);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to fetch student queue.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [riskLevel, semester, hasBacklogs, sortBy, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchStudents();
  };

  const riskCounts = data?.risk_counts || { ALL: 0, CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };

  const getTierBadgeStyle = (tier: string) => {
    switch (tier) {
      case 'CRITICAL':
        return { bg: 'rgba(147, 51, 234, 0.15)', text: '#D8B4FE', border: 'rgba(147, 51, 234, 0.4)' };
      case 'HIGH':
        return { bg: 'rgba(255, 45, 32, 0.15)', text: '#FF2D20', border: 'rgba(255, 45, 32, 0.4)' };
      case 'MEDIUM':
        return { bg: 'rgba(255, 183, 3, 0.15)', text: '#FFB703', border: 'rgba(255, 183, 3, 0.4)' };
      default:
        return { bg: 'rgba(85, 166, 48, 0.15)', text: '#55A630', border: 'rgba(85, 166, 48, 0.4)' };
    }
  };

  return (
    <div style={{ padding: '2rem 2.5rem', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ fontSize: '0.7rem', fontFamily: "'JetBrains Mono', monospace", color: '#6366F1', fontWeight: 600, letterSpacing: '0.08em', marginBottom: '0.35rem' }}>
            PRIORITY STUDENT QUEUE
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#FFFFFF', margin: 0, letterSpacing: '-0.02em' }}>
            Academic Intervention Attention Queue
          </h1>
          <div style={{ fontSize: '0.8rem', color: '#71717A', marginTop: '0.25rem' }}>
            Multi-factor composite priority ranking based on risk score, attendance deficits, backlogs, and performance trajectory.
          </div>
        </div>

        <button
          onClick={fetchStudents}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 0.9rem',
            backgroundColor: '#18181B',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '6px',
            color: '#E4E4E7',
            cursor: 'pointer',
            fontSize: '0.75rem',
            fontWeight: 600,
          }}
        >
          <RefreshCw size={14} />
          <span>REFRESH QUEUE</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div
        style={{
          backgroundColor: '#0A0A0C',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: '8px',
          padding: '1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}
      >
        {/* Risk Level Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, marginRight: '0.5rem', textTransform: 'uppercase' }}>
            Risk Filter:
          </span>
          {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((lvl) => {
            const isActive = riskLevel === lvl;
            const count = riskCounts[lvl] ?? 0;
            return (
              <button
                key={lvl}
                onClick={() => {
                  setRiskLevel(lvl);
                  setPage(1);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  padding: '0.4rem 0.75rem',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: isActive ? '1px solid #6366F1' : '1px solid rgba(255, 255, 255, 0.08)',
                  backgroundColor: isActive ? 'rgba(99, 102, 241, 0.2)' : '#121216',
                  color: isActive ? '#FFFFFF' : '#A1A1AA',
                  transition: 'all 0.15s ease',
                }}
              >
                <span>{lvl}</span>
                <span
                  style={{
                    fontSize: '0.65rem',
                    padding: '0.1rem 0.35rem',
                    borderRadius: '4px',
                    backgroundColor: isActive ? '#6366F1' : '#1E1E24',
                    color: '#FFFFFF',
                    fontFamily: "'JetBrains Mono', monospace",
                  }}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search & Select Controls */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1.5fr', gap: '0.75rem', alignItems: 'center' }}>
          {/* Search */}
          <form onSubmit={handleSearchSubmit} style={{ position: 'relative' }}>
            <Search size={16} color="#71717A" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search by Student ID or Name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem 0.55rem 2.25rem',
                backgroundColor: '#121216',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px',
                color: '#FFFFFF',
                fontSize: '0.8rem',
                outline: 'none',
              }}
            />
          </form>

          {/* Semester */}
          <select
            value={semester}
            onChange={(e) => {
              setSemester(e.target.value);
              setPage(1);
            }}
            style={{
              padding: '0.55rem 0.75rem',
              backgroundColor: '#121216',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              color: '#FFFFFF',
              fontSize: '0.8rem',
              outline: 'none',
            }}
          >
            <option value="">All Semesters</option>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
              <option key={s} value={s}>
                Semester {s}
              </option>
            ))}
          </select>

          {/* Backlogs */}
          <select
            value={hasBacklogs}
            onChange={(e) => {
              setHasBacklogs(e.target.value);
              setPage(1);
            }}
            style={{
              padding: '0.55rem 0.75rem',
              backgroundColor: '#121216',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              color: '#FFFFFF',
              fontSize: '0.8rem',
              outline: 'none',
            }}
          >
            <option value="">Backlogs: Any</option>
            <option value="yes">Has Active Backlogs</option>
            <option value="no">Zero Backlogs</option>
          </select>

          {/* Sorting */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <ArrowUpDown size={14} color="#71717A" />
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(1);
              }}
              style={{
                width: '100%',
                padding: '0.55rem 0.75rem',
                backgroundColor: '#121216',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px',
                color: '#FFFFFF',
                fontSize: '0.8rem',
                outline: 'none',
              }}
            >
              <option value="priority">Sort: Intervention Urgency (Priority)</option>
              <option value="risk_score_desc">Sort: Risk Score (High → Low)</option>
              <option value="cgpa_asc">Sort: Current CGPA (Low → High)</option>
              <option value="attendance_asc">Sort: Attendance (Low → High)</option>
              <option value="backlogs_desc">Sort: Backlogs (High → Low)</option>
              <option value="name_asc">Sort: Student Name (A → Z)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Student List Table */}
      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#71717A' }}>
          <RefreshCw size={20} className="animate-spin" color="#6366F1" style={{ margin: '0 auto 0.75rem auto' }} />
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.82rem' }}>
            COMPUTING PRIORITY RANKINGS & ATTENTION SCORES…
          </div>
        </div>
      ) : error ? (
        <div style={{ padding: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#FCA5A5' }}>
          {error}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div
          style={{
            padding: '3rem',
            textAlign: 'center',
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
          }}
        >
          <Users size={32} color="#52525B" style={{ margin: '0 auto 0.75rem auto' }} />
          <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#FFFFFF', marginBottom: '0.25rem' }}>
            NO MATCHING STUDENTS FOUND
          </div>
          <div style={{ fontSize: '0.8rem', color: '#71717A' }}>
            No student records match the active search and filter criteria.
          </div>
        </div>
      ) : (
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            overflow: 'hidden',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#0F0F12', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#71717A' }}>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>PRIORITY</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>STUDENT IDENTIFIER</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>CURRENT / PRED CGPA</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>RISK SCORE</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>ATTENDANCE</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>BACKLOGS</th>
                <th style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>KEY FACTORS</th>
                <th style={{ padding: '0.85rem 1rem', textAlign: 'right', fontWeight: 600 }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((student, idx) => {
                const rankNum = (page - 1) * limit + idx + 1;
                const tierStyle = getTierBadgeStyle(student.priority_tier);
                return (
                  <tr
                    key={student.id}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      transition: 'background 0.15s ease',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#121216')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                    onClick={() => navigate(`/faculty/students/${student.id}`)}
                  >
                    {/* Priority Tier */}
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.72rem', color: '#71717A', width: '20px' }}>
                          #{rankNum}
                        </span>
                        <span
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 700,
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            backgroundColor: tierStyle.bg,
                            color: tierStyle.text,
                            border: `1px solid ${tierStyle.border}`,
                            letterSpacing: '0.04em',
                          }}
                        >
                          {student.priority_tier} ({student.priority_score.toFixed(0)})
                        </span>
                      </div>
                    </td>

                    {/* Student Info */}
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <div style={{ fontWeight: 600, color: '#FFFFFF' }}>{student.name}</div>
                      <div style={{ fontSize: '0.72rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
                        {student.student_number} · Sem {student.current_semester} · {student.department_code || 'CSE'}
                      </div>
                    </td>

                    {/* CGPA */}
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ fontWeight: 700, color: '#FFFFFF' }}>
                          {student.current_cgpa !== null ? student.current_cgpa.toFixed(2) : '—'}
                        </span>
                        <span style={{ color: '#52525B' }}>→</span>
                        <span style={{ fontWeight: 700, color: '#6366F1' }}>
                          {student.predicted_cgpa !== null ? student.predicted_cgpa.toFixed(2) : '—'}
                        </span>
                        {student.cgpa_trend === 'IMPROVING' && <TrendingUp size={14} color="#10B981" />}
                        {student.cgpa_trend === 'DECLINING' && <TrendingDown size={14} color="#EF4444" />}
                        {student.cgpa_trend === 'STABLE' && <Minus size={14} color="#71717A" />}
                      </div>
                    </td>

                    {/* Risk Score */}
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span
                          style={{
                            fontWeight: 700,
                            color: student.risk_level === 'CRITICAL' ? '#D8B4FE' : student.risk_level === 'HIGH' ? '#FF2D20' : student.risk_level === 'MEDIUM' ? '#FFB703' : '#55A630',
                          }}
                        >
                          {student.risk_level}
                        </span>
                        <span style={{ fontSize: '0.72rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
                          ({student.risk_score.toFixed(1)})
                        </span>
                      </div>
                    </td>

                    {/* Attendance */}
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span
                        style={{
                          fontWeight: 600,
                          color: student.attendance_percentage !== null && student.attendance_percentage < 75 ? '#EF4444' : '#E4E4E7',
                        }}
                      >
                        {student.attendance_percentage !== null ? `${student.attendance_percentage.toFixed(1)}%` : '—'}
                      </span>
                    </td>

                    {/* Backlogs */}
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span
                        style={{
                          fontWeight: 600,
                          color: student.backlogs > 0 ? '#F59E0B' : '#71717A',
                        }}
                      >
                        {student.backlogs}
                      </span>
                    </td>

                    {/* Key Factors */}
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                        {student.top_risk_factors.length === 0 ? (
                          <span style={{ color: '#52525B', fontSize: '0.72rem' }}>Normal indicators</span>
                        ) : (
                          student.top_risk_factors.map((f, i) => (
                            <span
                              key={i}
                              style={{
                                fontSize: '0.65rem',
                                padding: '0.15rem 0.4rem',
                                borderRadius: '4px',
                                backgroundColor: '#18181B',
                                border: '1px solid rgba(255, 255, 255, 0.08)',
                                color: '#D4D4D8',
                              }}
                            >
                              {f}
                            </span>
                          ))
                        )}
                      </div>
                    </td>

                    {/* Action */}
                    <td style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/faculty/students/${student.id}`);
                        }}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          padding: '0.4rem 0.75rem',
                          backgroundColor: '#1E1E24',
                          border: '1px solid rgba(99, 102, 241, 0.3)',
                          borderRadius: '4px',
                          color: '#A5B4FC',
                          fontWeight: 600,
                          fontSize: '0.72rem',
                          cursor: 'pointer',
                        }}
                      >
                        <span>DOSSIER</span>
                        <ChevronRight size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination Controls */}
          {data.pages > 1 && (
            <div
              style={{
                padding: '1rem',
                borderTop: '1px solid rgba(255, 255, 255, 0.07)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.78rem',
                color: '#71717A',
              }}
            >
              <div>
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, data.total)} of {data.total} students
              </div>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  style={{
                    padding: '0.35rem 0.75rem',
                    backgroundColor: '#121216',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '4px',
                    color: page <= 1 ? '#52525B' : '#E4E4E7',
                    cursor: page <= 1 ? 'not-allowed' : 'pointer',
                  }}
                >
                  Previous
                </button>
                <button
                  disabled={page >= data.pages}
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  style={{
                    padding: '0.35rem 0.75rem',
                    backgroundColor: '#121216',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '4px',
                    color: page >= data.pages ? '#52525B' : '#E4E4E7',
                    cursor: page >= data.pages ? 'not-allowed' : 'pointer',
                  }}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
