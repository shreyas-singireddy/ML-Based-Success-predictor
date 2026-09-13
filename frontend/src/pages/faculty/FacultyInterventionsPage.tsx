import React, { useEffect, useState, useCallback } from 'react';
import {
  ClipboardList,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  User,
  Sparkles,
  ArrowRight,
  Info,
  X,
  Loader2,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { interventionApi } from '../../services/interventionApi';
import { facultyApi } from '../../services/facultyApi';
import {
  Intervention,
  InterventionStatus,
  InterventionCategory,
  InterventionPriority,
  InterventionDashboardStats,
  BeforeAfterComparison,
} from '../../types/intervention';
import { FacultyStudentSummary } from '../../types/faculty';

const CATEGORIES: { value: InterventionCategory; label: string }[] = [
  { value: 'ATTENDANCE_SUPPORT', label: 'Attendance Support' },
  { value: 'BACKLOG_SUPPORT', label: 'Backlog Clearing Support' },
  { value: 'EXAM_PREPARATION', label: 'Exam & Test Preparation' },
  { value: 'SUBJECT_SUPPORT', label: 'Subject / Concept Tutoring' },
  { value: 'STUDY_PLAN', label: 'Personalized Study Plan' },
  { value: 'ACADEMIC_COUNSELLING', label: 'Academic Counselling' },
  { value: 'FACULTY_MEETING', label: '1-on-1 Faculty Mentoring' },
  { value: 'PERFORMANCE_REVIEW', label: 'Periodic Performance Review' },
  { value: 'OTHER', label: 'Other Academic Action' },
];

const STATUS_CONFIG: Record<
  InterventionStatus,
  { label: string; bg: string; text: string; border: string }
> = {
  PLANNED: { label: 'Planned', bg: 'rgba(113, 113, 122, 0.15)', text: '#A1A1AA', border: 'rgba(113, 113, 122, 0.3)' },
  SCHEDULED: { label: 'Scheduled', bg: 'rgba(59, 130, 246, 0.15)', text: '#93C5FD', border: 'rgba(59, 130, 246, 0.3)' },
  IN_PROGRESS: { label: 'In Progress', bg: 'rgba(234, 179, 8, 0.15)', text: '#FDE047', border: 'rgba(234, 179, 8, 0.3)' },
  FOLLOW_UP_REQUIRED: { label: 'Follow-up Due', bg: 'rgba(249, 115, 22, 0.15)', text: '#FDBA74', border: 'rgba(249, 115, 22, 0.3)' },
  COMPLETED: { label: 'Completed', bg: 'rgba(34, 197, 94, 0.15)', text: '#86EFAC', border: 'rgba(34, 197, 94, 0.3)' },
  CANCELLED: { label: 'Cancelled', bg: 'rgba(239, 68, 68, 0.15)', text: '#FCA5A5', border: 'rgba(239, 68, 68, 0.3)' },
};

const PRIORITY_CONFIG: Record<
  InterventionPriority,
  { label: string; bg: string; text: string }
> = {
  LOW: { label: 'Low', bg: 'rgba(113, 113, 122, 0.2)', text: '#A1A1AA' },
  MEDIUM: { label: 'Medium', bg: 'rgba(59, 130, 246, 0.2)', text: '#93C5FD' },
  HIGH: { label: 'High', bg: 'rgba(249, 115, 22, 0.2)', text: '#FDBA74' },
  CRITICAL: { label: 'Critical', bg: 'rgba(239, 68, 68, 0.25)', text: '#FCA5A5' },
};

export const FacultyInterventionsPage: React.FC = () => {
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [stats, setStats] = useState<InterventionDashboardStats | null>(null);
  const [students, setStudents] = useState<FacultyStudentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState<Intervention | null>(null);
  const [showFollowUpModal, setShowFollowUpModal] = useState<Intervention | null>(null);
  const [showOutcomeModal, setShowOutcomeModal] = useState<Intervention | null>(null);
  const [showComparisonModal, setShowComparisonModal] = useState<BeforeAfterComparison | null>(null);

  // Create Form state
  const [createForm, setCreateForm] = useState({
    student_id: '',
    category: 'ACADEMIC_COUNSELLING' as InterventionCategory,
    title: '',
    description: '',
    reason: '',
    priority: 'MEDIUM' as InterventionPriority,
    status: 'PLANNED' as InterventionStatus,
    notes: '',
    scheduled_at: '',
    follow_up_date: '',
  });

  // Action forms
  const [completeNotes, setCompleteNotes] = useState('');
  const [completeFollowUpDate, setCompleteFollowUpDate] = useState('');
  const [followUpNotes, setFollowUpNotes] = useState('');
  const [outcomeNotes, setOutcomeNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [listRes, statsRes, studentsRes] = await Promise.all([
        interventionApi.listInterventions({
          status: (statusFilter as InterventionStatus) || undefined,
          category: (categoryFilter as InterventionCategory) || undefined,
          priority: (priorityFilter as InterventionPriority) || undefined,
          search: searchQuery || undefined,
          page_size: 50,
        }),
        interventionApi.getDashboardStats(),
        facultyApi.getStudents({ limit: 100 }),
      ]);
      setInterventions(listRes.items);
      setStats(statsRes);
      setStudents(studentsRes.items);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load intervention records.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, categoryFilter, priorityFilter, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.student_id || !createForm.title || !createForm.description) {
      alert('Please select a student and provide a title and description.');
      return;
    }
    setIsSubmitting(true);
    try {
      await interventionApi.createIntervention({
        student_id: createForm.student_id,
        category: createForm.category,
        title: createForm.title,
        description: createForm.description,
        reason: createForm.reason || undefined,
        priority: createForm.priority,
        status: createForm.status,
        notes: createForm.notes || undefined,
        scheduled_at: createForm.scheduled_at ? new Date(createForm.scheduled_at).toISOString() : undefined,
        follow_up_date: createForm.follow_up_date ? new Date(createForm.follow_up_date).toISOString() : undefined,
      });
      setShowCreateModal(false);
      setCreateForm({
        student_id: '',
        category: 'ACADEMIC_COUNSELLING',
        title: '',
        description: '',
        reason: '',
        priority: 'MEDIUM',
        status: 'PLANNED',
        notes: '',
        scheduled_at: '',
        follow_up_date: '',
      });
      await loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create intervention.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleComplete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showCompleteModal) return;
    setIsSubmitting(true);
    try {
      await interventionApi.completeIntervention(showCompleteModal.id, {
        completion_notes: completeNotes || undefined,
        follow_up_date: completeFollowUpDate ? new Date(completeFollowUpDate).toISOString() : undefined,
      });
      setShowCompleteModal(null);
      setCompleteNotes('');
      setCompleteFollowUpDate('');
      await loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to complete intervention.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFollowUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showFollowUpModal || !followUpNotes) return;
    setIsSubmitting(true);
    try {
      await interventionApi.recordFollowUp(showFollowUpModal.id, {
        follow_up_notes: followUpNotes,
        status: 'COMPLETED',
      });
      setShowFollowUpModal(null);
      setFollowUpNotes('');
      await loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to record follow-up.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRecordOutcome = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showOutcomeModal) return;
    setIsSubmitting(true);
    try {
      await interventionApi.recordOutcome(showOutcomeModal.id, {
        notes: outcomeNotes || undefined,
      });
      setShowOutcomeModal(null);
      setOutcomeNotes('');
      await loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to record outcome measurement.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openComparison = async (interventionId: string) => {
    try {
      const comp = await interventionApi.getComparison(interventionId);
      setShowComparisonModal(comp);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to load before/after evaluation.');
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto', color: '#FFFFFF' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
            <span
              style={{
                fontSize: '0.7rem',
                fontFamily: "'JetBrains Mono', monospace",
                color: '#6366F1',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
              }}
            >
              PHASE 12 DECISION SUPPORT
            </span>
            <span style={{ fontSize: '0.75rem', color: '#71717A' }}>Observational Tracking & Outcomes</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>
            Intervention Tracking & Outcome Management
          </h1>
          <p style={{ color: '#A1A1AA', fontSize: '0.875rem', margin: '0.35rem 0 0 0' }}>
            Record structured faculty actions, track follow-up progress, and evaluate academic indicator trajectories.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => loadData()}
            style={{
              padding: '0.6rem 0.9rem',
              backgroundColor: '#18181B',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              color: '#E4E4E7',
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              padding: '0.6rem 1.1rem',
              background: 'linear-gradient(135deg, #6366F1 0%, #4338CA 100%)',
              border: 'none',
              borderRadius: '6px',
              color: '#FFFFFF',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 0 16px rgba(99, 102, 241, 0.35)',
            }}
          >
            <Plus size={16} />
            New Intervention
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      {stats && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '1rem',
            marginBottom: '2rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#0F0F11',
              border: '1px solid rgba(255, 255, 255, 0.07)',
              borderRadius: '8px',
              padding: '1.25rem',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Total Interventions
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.35rem', color: '#FFFFFF' }}>
              {stats.total_interventions}
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#0F0F11',
              border: '1px solid rgba(234, 179, 8, 0.2)',
              borderRadius: '8px',
              padding: '1.25rem',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: '#FDE047', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Active / In Progress
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.35rem', color: '#FDE047' }}>
              {stats.active_interventions}
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#0F0F11',
              border: '1px solid rgba(249, 115, 22, 0.25)',
              borderRadius: '8px',
              padding: '1.25rem',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: '#FDBA74', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Follow-ups Due
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.35rem', color: '#FDBA74' }}>
              {stats.follow_ups_due}
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#0F0F11',
              border: '1px solid rgba(34, 197, 94, 0.2)',
              borderRadius: '8px',
              padding: '1.25rem',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: '#86EFAC', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Completed Actions
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.35rem', color: '#86EFAC' }}>
              {stats.completed_interventions}
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#0F0F11',
              border: '1px solid rgba(99, 102, 241, 0.2)',
              borderRadius: '8px',
              padding: '1.25rem',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: '#A5B4FC', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Improved Indicators
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.35rem', color: '#A5B4FC' }}>
              {stats.improved_count}
              <span style={{ fontSize: '0.8rem', color: '#71717A', marginLeft: '0.5rem', fontWeight: 400 }}>
                ({stats.stable_count} stable)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Filter & Search Toolbar */}
      <div
        style={{
          backgroundColor: '#0F0F11',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1 1 260px' }}>
          <div
            style={{
              position: 'relative',
              width: '100%',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Search size={16} color="#71717A" style={{ position: 'absolute', left: '0.8rem' }} />
            <input
              type="text"
              placeholder="Search by student name, number, or title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '0.55rem 0.8rem 0.55rem 2.4rem',
                backgroundColor: '#18181B',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                outline: 'none',
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '0.55rem 0.8rem',
              backgroundColor: '#18181B',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              color: '#FFFFFF',
              fontSize: '0.85rem',
              outline: 'none',
            }}
          >
            <option value="">All Statuses</option>
            <option value="PLANNED">Planned</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="FOLLOW_UP_REQUIRED">Follow-up Due</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{
              padding: '0.55rem 0.8rem',
              backgroundColor: '#18181B',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              color: '#FFFFFF',
              fontSize: '0.85rem',
              outline: 'none',
            }}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            style={{
              padding: '0.55rem 0.8rem',
              backgroundColor: '#18181B',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              color: '#FFFFFF',
              fontSize: '0.85rem',
              outline: 'none',
            }}
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Main List */}
      {isLoading ? (
        <div
          style={{
            padding: '4rem',
            textAlign: 'center',
            backgroundColor: '#0F0F11',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            color: '#71717A',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '0.85rem',
          }}
        >
          <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#6366F1' }} />
          LOADING INTERVENTION RECORDS...
        </div>
      ) : error ? (
        <div
          style={{
            padding: '2rem',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            color: '#FCA5A5',
          }}
        >
          {error}
        </div>
      ) : interventions.length === 0 ? (
        <div
          style={{
            padding: '4rem 2rem',
            textAlign: 'center',
            backgroundColor: '#0F0F11',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.07)',
          }}
        >
          <ClipboardList size={40} color="#52525B" style={{ margin: '0 auto 1rem auto' }} />
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#E4E4E7' }}>NO ACTIVE INTERVENTIONS</div>
          <p style={{ color: '#71717A', fontSize: '0.85rem', maxWidth: '400px', margin: '0.5rem auto 1.5rem auto' }}>
            No interventions match the selected filter criteria. Create a targeted intervention to begin tracking student support.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              padding: '0.55rem 1rem',
              backgroundColor: '#6366F1',
              border: 'none',
              borderRadius: '6px',
              color: '#FFFFFF',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Create First Intervention
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {interventions.map((inv) => {
            const stCfg = STATUS_CONFIG[inv.status] || STATUS_CONFIG.PLANNED;
            const prCfg = PRIORITY_CONFIG[inv.priority] || PRIORITY_CONFIG.MEDIUM;

            return (
              <div
                key={inv.id}
                style={{
                  backgroundColor: '#0F0F11',
                  border: '1px solid rgba(255, 255, 255, 0.07)',
                  borderRadius: '8px',
                  padding: '1.5rem',
                  transition: 'border-color 0.15s ease',
                }}
              >
                {/* Top Row: Meta Badges */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                    marginBottom: '0.75rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        backgroundColor: stCfg.bg,
                        color: stCfg.text,
                        border: `1px solid ${stCfg.border}`,
                        fontFamily: "'JetBrains Mono', monospace",
                      }}
                    >
                      {stCfg.label}
                    </span>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        backgroundColor: prCfg.bg,
                        color: prCfg.text,
                        fontFamily: "'JetBrains Mono', monospace",
                      }}
                    >
                      {prCfg.label} Priority
                    </span>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        color: '#A1A1AA',
                        backgroundColor: '#18181B',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                      }}
                    >
                      {inv.category.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.75rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
                    Created: {new Date(inv.created_at).toLocaleDateString()}
                  </div>
                </div>

                {/* Title and Reason */}
                <div style={{ marginBottom: '0.75rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0 0 0.35rem 0', color: '#FFFFFF' }}>
                    {inv.title}
                  </h3>
                  <p style={{ color: '#D4D4D8', fontSize: '0.875rem', margin: 0, lineHeight: 1.5 }}>
                    {inv.description}
                  </p>
                  {inv.reason && (
                    <div
                      style={{
                        marginTop: '0.5rem',
                        padding: '0.4rem 0.65rem',
                        backgroundColor: '#141418',
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        color: '#A1A1AA',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                      }}
                    >
                      <Info size={14} color="#6366F1" />
                      <span><strong>Linked Reason:</strong> {inv.reason}</span>
                    </div>
                  )}
                </div>

                {/* Student & Baseline Grid */}
                <div
                  style={{
                    backgroundColor: '#141418',
                    borderRadius: '6px',
                    padding: '0.85rem 1rem',
                    marginBottom: '1rem',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: '1rem',
                    fontSize: '0.8rem',
                  }}
                >
                  <div>
                    <div style={{ color: '#71717A', fontSize: '0.7rem', textTransform: 'uppercase' }}>Student</div>
                    <div style={{ fontWeight: 600, color: '#FFFFFF', marginTop: '0.15rem' }}>
                      {inv.student_name || 'N/A'}
                    </div>
                    <div style={{ color: '#71717A', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem' }}>
                      {inv.student_number} • {inv.department_name || 'Department'}
                    </div>
                  </div>

                  <div>
                    <div style={{ color: '#71717A', fontSize: '0.7rem', textTransform: 'uppercase' }}>Baseline Risk</div>
                    <div
                      style={{
                        fontWeight: 600,
                        color: inv.baseline_risk_level === 'HIGH' || inv.baseline_risk_level === 'CRITICAL' ? '#FCA5A5' : '#86EFAC',
                        marginTop: '0.15rem',
                      }}
                    >
                      {inv.baseline_risk_level || 'N/A'}
                    </div>
                    <div style={{ color: '#71717A', fontSize: '0.75rem' }}>
                      Predicted CGPA: {inv.baseline_predicted_cgpa !== undefined && inv.baseline_predicted_cgpa !== null ? inv.baseline_predicted_cgpa.toFixed(2) : 'N/A'}
                    </div>
                  </div>

                  <div>
                    <div style={{ color: '#71717A', fontSize: '0.7rem', textTransform: 'uppercase' }}>Baseline Attendance</div>
                    <div style={{ fontWeight: 600, color: '#FFFFFF', marginTop: '0.15rem' }}>
                      {inv.baseline_attendance !== undefined && inv.baseline_attendance !== null ? `${inv.baseline_attendance.toFixed(1)}%` : 'N/A'}
                    </div>
                    <div style={{ color: '#71717A', fontSize: '0.75rem' }}>
                      Backlogs: {inv.baseline_backlogs !== undefined && inv.baseline_backlogs !== null ? inv.baseline_backlogs : 0}
                    </div>
                  </div>

                  <div>
                    <div style={{ color: '#71717A', fontSize: '0.7rem', textTransform: 'uppercase' }}>Follow-up Schedule</div>
                    <div style={{ fontWeight: 600, color: '#FDBA74', marginTop: '0.15rem' }}>
                      {inv.follow_up_date ? new Date(inv.follow_up_date).toLocaleDateString() : 'None Scheduled'}
                    </div>
                    {inv.completed_at && (
                      <div style={{ color: '#86EFAC', fontSize: '0.75rem' }}>
                        Completed: {new Date(inv.completed_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>

                {/* Outcome Banner (if measured) */}
                {inv.outcome && (
                  <div
                    style={{
                      padding: '0.75rem 1rem',
                      borderRadius: '6px',
                      marginBottom: '1rem',
                      backgroundColor:
                        inv.outcome.outcome_status === 'IMPROVED'
                          ? 'rgba(34, 197, 94, 0.1)'
                          : inv.outcome.outcome_status === 'DECLINED'
                          ? 'rgba(239, 68, 68, 0.1)'
                          : 'rgba(59, 130, 246, 0.1)',
                      border:
                        inv.outcome.outcome_status === 'IMPROVED'
                          ? '1px solid rgba(34, 197, 94, 0.3)'
                          : inv.outcome.outcome_status === 'DECLINED'
                          ? '1px solid rgba(239, 68, 68, 0.3)'
                          : '1px solid rgba(59, 130, 246, 0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      {inv.outcome.outcome_status === 'IMPROVED' ? (
                        <TrendingUp size={16} color="#86EFAC" />
                      ) : inv.outcome.outcome_status === 'DECLINED' ? (
                        <TrendingDown size={16} color="#FCA5A5" />
                      ) : (
                        <Minus size={16} color="#93C5FD" />
                      )}
                      <div>
                        <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                          Measured Indicator Trajectory: {inv.outcome.outcome_status}
                        </span>
                        <div style={{ fontSize: '0.75rem', color: '#A1A1AA' }}>
                          Current CGPA: {inv.outcome.current_predicted_cgpa?.toFixed(2) || 'N/A'} • Attendance: {inv.outcome.current_attendance?.toFixed(1) || 'N/A'}% • Backlogs: {inv.outcome.current_backlogs ?? 'N/A'}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => openComparison(inv.id)}
                      style={{
                        padding: '0.35rem 0.65rem',
                        backgroundColor: '#18181B',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '4px',
                        color: '#FFFFFF',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      View Before/After Delta
                      <ArrowRight size={12} />
                    </button>
                  </div>
                )}

                {/* Bottom Action Buttons */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'flex-end' }}>
                  {inv.status !== 'COMPLETED' && inv.status !== 'CANCELLED' && (
                    <button
                      onClick={() => setShowCompleteModal(inv)}
                      style={{
                        padding: '0.45rem 0.8rem',
                        backgroundColor: '#18181B',
                        border: '1px solid rgba(34, 197, 94, 0.4)',
                        borderRadius: '4px',
                        color: '#86EFAC',
                        fontSize: '0.8rem',
                        fontWeight: 500,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      <CheckCircle2 size={14} />
                      Complete Intervention
                    </button>
                  )}

                  {inv.status === 'FOLLOW_UP_REQUIRED' && (
                    <button
                      onClick={() => setShowFollowUpModal(inv)}
                      style={{
                        padding: '0.45rem 0.8rem',
                        backgroundColor: '#18181B',
                        border: '1px solid rgba(249, 115, 22, 0.4)',
                        borderRadius: '4px',
                        color: '#FDBA74',
                        fontSize: '0.8rem',
                        fontWeight: 500,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      <Clock size={14} />
                      Record Follow-up
                    </button>
                  )}

                  <button
                    onClick={() => setShowOutcomeModal(inv)}
                    style={{
                      padding: '0.45rem 0.8rem',
                      backgroundColor: '#18181B',
                      border: '1px solid rgba(99, 102, 241, 0.4)',
                      borderRadius: '4px',
                      color: '#A5B4FC',
                      fontSize: '0.8rem',
                      fontWeight: 500,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                    }}
                  >
                    <Sparkles size={14} />
                    Evaluate Outcome
                  </button>

                  <button
                    onClick={() => openComparison(inv.id)}
                    style={{
                      padding: '0.45rem 0.8rem',
                      backgroundColor: '#18181B',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '4px',
                      color: '#E4E4E7',
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                    }}
                  >
                    Full Comparison
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Non-causal Observational Disclaimer Banner */}
      <div
        style={{
          marginTop: '3rem',
          padding: '1rem 1.25rem',
          backgroundColor: '#0C0C0E',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          color: '#71717A',
          fontSize: '0.75rem',
          lineHeight: 1.5,
        }}
      >
        <Info size={16} color="#6366F1" style={{ flexShrink: 0 }} />
        <div>
          <strong>Observational Decision Support Disclaimer:</strong> Outcome measurements represent measured indicator changes after interventions were recorded. The system does not assert deterministic causality. Academic performance depends on multifaceted student and instructional factors.
        </div>
      </div>

      {/* CREATE MODAL */}
      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#121216',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              maxWidth: '640px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>Create Academic Intervention</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{ background: 'none', border: 'none', color: '#71717A', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label htmlFor="target-student-select" style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                  Select Target Student *
                </label>
                <select
                  id="target-student-select"
                  value={createForm.student_id}
                  onChange={(e) => setCreateForm({ ...createForm, student_id: e.target.value })}
                  required
                  style={{

                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontSize: '0.85rem',
                  }}
                >
                  <option value="">-- Choose student from assigned department --</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.student_number}) • Risk: {s.risk_level} • CGPA: {s.current_cgpa?.toFixed(2) || 'N/A'}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                    Intervention Category *
                  </label>
                  <select
                    value={createForm.category}
                    onChange={(e) => setCreateForm({ ...createForm, category: e.target.value as InterventionCategory })}
                    style={{
                      width: '100%',
                      padding: '0.6rem 0.8rem',
                      backgroundColor: '#18181B',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '6px',
                      color: '#FFFFFF',
                      fontSize: '0.85rem',
                    }}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                    Priority *
                  </label>
                  <select
                    value={createForm.priority}
                    onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value as InterventionPriority })}
                    style={{
                      width: '100%',
                      padding: '0.6rem 0.8rem',
                      backgroundColor: '#18181B',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '6px',
                      color: '#FFFFFF',
                      fontSize: '0.85rem',
                    }}
                  >
                    <option value="LOW">Low Priority</option>
                    <option value="MEDIUM">Medium Priority</option>
                    <option value="HIGH">High Priority</option>
                    <option value="CRITICAL">Critical Priority</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                  Title / Action Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Attendance & Mid-term Revision Mentoring"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                  Description / Action Plan *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Detail the agreed intervention steps, remedial topics, or study schedule..."
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontSize: '0.85rem',
                    resize: 'vertical',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                  Evidence / Linked Reason (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Attendance declined from 82% to 68%; 1 backlog in Applied Physics"
                  value={createForm.reason}
                  onChange={(e) => setCreateForm({ ...createForm, reason: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                    Scheduled Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={createForm.scheduled_at}
                    onChange={(e) => setCreateForm({ ...createForm, scheduled_at: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.6rem 0.8rem',
                      backgroundColor: '#18181B',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '6px',
                      color: '#FFFFFF',
                      fontSize: '0.85rem',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                    Follow-up Target Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={createForm.follow_up_date}
                    onChange={(e) => setCreateForm({ ...createForm, follow_up_date: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '0.6rem 0.8rem',
                      backgroundColor: '#18181B',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '6px',
                      color: '#FFFFFF',
                      fontSize: '0.85rem',
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  style={{
                    padding: '0.6rem 1rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#E4E4E7',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    padding: '0.6rem 1.25rem',
                    background: 'linear-gradient(135deg, #6366F1 0%, #4338CA 100%)',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  {isSubmitting ? 'Creating...' : 'Record Intervention'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* COMPLETE MODAL */}
      {showCompleteModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#121216',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              maxWidth: '520px',
              width: '100%',
              padding: '1.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>Complete Intervention</h2>
              <button
                onClick={() => setShowCompleteModal(null)}
                style={{ background: 'none', border: 'none', color: '#71717A', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <p style={{ color: '#A1A1AA', fontSize: '0.85rem', marginBottom: '1rem' }}>
              Mark "{showCompleteModal.title}" as completed. You can also schedule an optional future follow-up check.
            </p>

            <form onSubmit={handleComplete} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                  Completion Summary Notes
                </label>
                <textarea
                  rows={3}
                  placeholder="Record summary of what was covered and student response..."
                  value={completeNotes}
                  onChange={(e) => setCompleteNotes(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                  Schedule Follow-up Date (Optional)
                </label>
                <input
                  type="date"
                  value={completeFollowUpDate}
                  onChange={(e) => setCompleteFollowUpDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCompleteModal(null)}
                  style={{
                    padding: '0.6rem 1rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#E4E4E7',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    padding: '0.6rem 1.25rem',
                    backgroundColor: '#22C55E',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  {isSubmitting ? 'Saving...' : 'Confirm Completion'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* FOLLOW-UP MODAL */}
      {showFollowUpModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#121216',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              maxWidth: '520px',
              width: '100%',
              padding: '1.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>Record Follow-up Progress</h2>
              <button
                onClick={() => setShowFollowUpModal(null)}
                style={{ background: 'none', border: 'none', color: '#71717A', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleFollowUp} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                  Follow-up Observation Notes *
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Record observed progress, student adherence, updated attendance, or test scores..."
                  value={followUpNotes}
                  onChange={(e) => setFollowUpNotes(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setShowFollowUpModal(null)}
                  style={{
                    padding: '0.6rem 1rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#E4E4E7',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    padding: '0.6rem 1.25rem',
                    backgroundColor: '#F97316',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  {isSubmitting ? 'Saving...' : 'Save Follow-up'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EVALUATE OUTCOME MODAL */}
      {showOutcomeModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#121216',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              maxWidth: '520px',
              width: '100%',
              padding: '1.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>Evaluate Indicator Outcome</h2>
              <button
                onClick={() => setShowOutcomeModal(null)}
                style={{ background: 'none', border: 'none', color: '#71717A', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <p style={{ color: '#A1A1AA', fontSize: '0.85rem', marginBottom: '1rem', lineHeight: 1.5 }}>
              The system will dynamically measure the student's current indicators (risk category, predicted CGPA, attendance rate, backlogs count) and compare them with the baseline snapshot.
            </p>

            <form onSubmit={handleRecordOutcome} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#A1A1AA', marginBottom: '0.35rem' }}>
                  Faculty Evaluation Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Additional context on observed student development..."
                  value={outcomeNotes}
                  onChange={(e) => setOutcomeNotes(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setShowOutcomeModal(null)}
                  style={{
                    padding: '0.6rem 1rem',
                    backgroundColor: '#18181B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    color: '#E4E4E7',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    padding: '0.6rem 1.25rem',
                    background: 'linear-gradient(135deg, #6366F1 0%, #4338CA 100%)',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#FFFFFF',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  {isSubmitting ? 'Measuring...' : 'Measure & Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* COMPARISON / DELTA MODAL */}
      {showComparisonModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#121216',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              maxWidth: '680px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
                  Before vs. After Indicator Evaluation
                </h2>
                <div style={{ fontSize: '0.8rem', color: '#A1A1AA', marginTop: '0.2rem' }}>
                  {showComparisonModal.student_name} ({showComparisonModal.student_number})
                </div>
              </div>
              <button
                onClick={() => setShowComparisonModal(null)}
                style={{ background: 'none', border: 'none', color: '#71717A', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Observational Statement Box */}
            <div
              style={{
                padding: '1rem',
                borderRadius: '6px',
                marginBottom: '1.25rem',
                backgroundColor:
                  showComparisonModal.outcome_status === 'IMPROVED'
                    ? 'rgba(34, 197, 94, 0.1)'
                    : showComparisonModal.outcome_status === 'DECLINED'
                    ? 'rgba(239, 68, 68, 0.1)'
                    : 'rgba(59, 130, 246, 0.1)',
                border:
                  showComparisonModal.outcome_status === 'IMPROVED'
                    ? '1px solid rgba(34, 197, 94, 0.3)'
                    : showComparisonModal.outcome_status === 'DECLINED'
                    ? '1px solid rgba(239, 68, 68, 0.3)'
                    : '1px solid rgba(59, 130, 246, 0.3)',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: '#A1A1AA', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Outcome Status: {showComparisonModal.outcome_status}
              </div>
              <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#FFFFFF', marginTop: '0.25rem' }}>
                "{showComparisonModal.observational_statement}"
              </div>
            </div>

            {/* Indicators Table */}
            <div style={{ marginBottom: '1.25rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#71717A', textAlign: 'left' }}>
                    <th style={{ padding: '0.6rem 0.5rem' }}>Tracked Metric</th>
                    <th style={{ padding: '0.6rem 0.5rem' }}>Baseline (Before)</th>
                    <th style={{ padding: '0.6rem 0.5rem' }}>Follow-up (After)</th>
                    <th style={{ padding: '0.6rem 0.5rem' }}>Measured Delta</th>
                    <th style={{ padding: '0.6rem 0.5rem' }}>Indicator Status</th>
                  </tr>
                </thead>
                <tbody>
                  {showComparisonModal.indicators.map((ind, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                      <td style={{ padding: '0.6rem 0.5rem', fontWeight: 500, color: '#E4E4E7' }}>{ind.indicator}</td>
                      <td style={{ padding: '0.6rem 0.5rem', color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                        {ind.before ?? 'N/A'}
                      </td>
                      <td style={{ padding: '0.6rem 0.5rem', color: '#FFFFFF', fontFamily: "'JetBrains Mono', monospace" }}>
                        {ind.after ?? 'Pending'}
                      </td>
                      <td
                        style={{
                          padding: '0.6rem 0.5rem',
                          fontFamily: "'JetBrains Mono', monospace",
                          fontWeight: 600,
                          color:
                            ind.status === 'IMPROVED'
                              ? '#86EFAC'
                              : ind.status === 'DECLINED'
                              ? '#FCA5A5'
                              : '#93C5FD',
                        }}
                      >
                        {ind.delta ?? 'N/A'}
                      </td>
                      <td style={{ padding: '0.6rem 0.5rem' }}>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            padding: '0.15rem 0.4rem',
                            borderRadius: '3px',
                            backgroundColor:
                              ind.status === 'IMPROVED'
                                ? 'rgba(34, 197, 94, 0.15)'
                                : ind.status === 'DECLINED'
                                ? 'rgba(239, 68, 68, 0.15)'
                                : 'rgba(59, 130, 246, 0.15)',
                            color:
                              ind.status === 'IMPROVED'
                                ? '#86EFAC'
                                : ind.status === 'DECLINED'
                                ? '#FCA5A5'
                                : '#93C5FD',
                          }}
                        >
                          {ind.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Disclaimer */}
            <div
              style={{
                padding: '0.85rem',
                backgroundColor: '#0A0A0C',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                color: '#71717A',
                fontSize: '0.75rem',
                lineHeight: 1.4,
              }}
            >
              {showComparisonModal.disclaimer}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
              <button
                onClick={() => setShowComparisonModal(null)}
                style={{
                  padding: '0.55rem 1.25rem',
                  backgroundColor: '#18181B',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: '#FFFFFF',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
