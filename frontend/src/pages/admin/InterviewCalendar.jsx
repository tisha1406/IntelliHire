import { useState, useEffect } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import Button from "../../components/common/Button";
import { MonitoringAPI } from "../../api/monitoring";
import "../../styles/admin/calendar.css";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];

const eventColors = { scheduled: '#2563EB', upcoming: '#f59e0b', completed: '#22c55e', cancelled: '#ef4444', invited: '#f59e0b', abandoned: '#ef4444' };
const eventBg = { scheduled: 'rgba(37,99,235,0.12)', upcoming: 'rgba(245,158,11,0.12)', completed: 'rgba(34,197,94,0.12)', cancelled: 'rgba(239,68,68,0.12)', invited: 'rgba(245,158,11,0.12)', abandoned: 'rgba(239,68,68,0.12)' };

function getDaysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
}

export default function InterviewCalendar() {
    const now = new Date();
    const [viewDate, setViewDate] = useState({ year: now.getFullYear(), month: now.getMonth() });
    const [view, setView] = useState("month");
    const [selectedDay, setSelectedDay] = useState(null);
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchEvents = async () => {
            try {
                const data = await MonitoringAPI.getCalendarEvents();
                // Format dates to YYYY-MM-DD
                const formattedEvents = data.map(ev => {
                    const dateObj = new Date(ev.start);
                    const yyyy = dateObj.getFullYear();
                    const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
                    const dd = String(dateObj.getDate()).padStart(2, '0');
                    const time = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    return { ...ev, date: `${yyyy}-${mm}-${dd}`, time, type: ev.status.toLowerCase() };
                });
                setEvents(formattedEvents);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchEvents();
    }, []);

    const { year, month } = viewDate;
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = getDaysInMonth(year, month);

    const prev = () => setViewDate(v => v.month === 0 ? { year: v.year - 1, month: 11 } : { ...v, month: v.month - 1 });
    const next = () => setViewDate(v => v.month === 11 ? { year: v.year + 1, month: 0 } : { ...v, month: v.month + 1 });

    const getEventsForDay = (day) => {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        return events.filter(e => e.date === dateStr);
    };

    const selectedEvents = selectedDay ? getEventsForDay(selectedDay) : [];

    const todayDay = now.getDate();
    const isCurrentMonth = now.getFullYear() === year && now.getMonth() === month;

    const eventCounts = { scheduled: 0, invited: 0, completed: 0, abandoned: 0 };
    events.forEach(e => { 
        if(eventCounts[e.type] !== undefined) eventCounts[e.type]++; 
    });

    return (
        <DashboardGrid>
            <PageHeader
                title="Interview Calendar"
                description="View and track all scheduled, completed, and upcoming AI interviews."
                rightContent={
                    <div style={{ display: 'flex', gap: '8px' }}>
                        {["month", "week", "day"].map(v => (
                            <Button key={v} variant={view === v ? "primary" : "outline"} size="sm" onClick={() => setView(v)}
                                style={{ textTransform: 'capitalize' }}>{v}</Button>
                        ))}
                    </div>
                }
            />

            <StatGrid>
                {Object.entries(eventCounts).map(([type, count]) => (
                    <Card key={type} className="ih-card">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: eventColors[type] || 'var(--primary)' }} />
                            <div style={{ color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'capitalize' }}>{type}</div>
                        </div>
                        <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>{count}</div>
                    </Card>
                ))}
            </StatGrid>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px', alignItems: 'start' }}>
                <SectionCard>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                        <h2 style={{ fontSize: '18px', fontWeight: '600', color: 'var(--text)' }}>
                            {MONTHS[month]} {year}
                        </h2>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button onClick={prev} className="cal-nav-btn"><ChevronLeft size={18} /></button>
                            <button onClick={() => setViewDate({ year: now.getFullYear(), month: now.getMonth() })}
                                style={{ padding: '6px 14px', borderRadius: '6px', border: '1px solid var(--border)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '13px' }}>
                                Today
                            </button>
                            <button onClick={next} className="cal-nav-btn"><ChevronRight size={18} /></button>
                        </div>
                    </div>

                    <div className="cal-grid-header">
                        {DAYS.map(d => <div key={d} className="cal-day-header">{d}</div>)}
                    </div>

                    <div className="cal-grid">
                        {Array.from({ length: firstDay }).map((_, i) => (
                            <div key={`empty-${i}`} className="cal-day cal-day-empty" />
                        ))}
                        {Array.from({ length: daysInMonth }).map((_, i) => {
                            const day = i + 1;
                            const dayEvents = getEventsForDay(day);
                            const isToday = isCurrentMonth && day === todayDay;
                            const isSelected = selectedDay === day;
                            return (
                                <div
                                    key={day}
                                    className={`cal-day ${isToday ? 'cal-day-today' : ''} ${isSelected ? 'cal-day-selected' : ''}`}
                                    onClick={() => setSelectedDay(isSelected ? null : day)}
                                >
                                    <span className="cal-day-num">{day}</span>
                                    <div className="cal-events">
                                        {dayEvents.slice(0, 2).map((ev, idx) => (
                                            <div key={idx} className="cal-event-dot" style={{ background: eventColors[ev.type] || 'var(--primary)' }} />
                                        ))}
                                        {dayEvents.length > 2 && (
                                            <span className="cal-event-more">+{dayEvents.length - 2}</span>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </SectionCard>

                <SectionCard>
                    <h4 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text)', marginBottom: '16px' }}>
                        {selectedDay ? `Events on ${MONTHS[month]} ${selectedDay}` : 'Upcoming Interviews'}
                    </h4>
                    {loading ? <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Loading events...</div> : (selectedDay ? selectedEvents : events.filter(e => e.type === 'upcoming' || e.type === 'scheduled' || e.type === 'invited').slice(0, 5)).map((ev, i) => (
                        <div key={i} style={{ padding: '12px', background: eventBg[ev.type] || 'var(--primary-subtle)', borderRadius: '8px', border: `1px solid ${eventColors[ev.type] || 'var(--primary)'}30`, marginBottom: '10px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span style={{ fontSize: '12px', fontWeight: '600', color: eventColors[ev.type] || 'var(--primary)', textTransform: 'capitalize' }}>{ev.type}</span>
                                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{ev.time}</span>
                            </div>
                            <div style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text)' }}>{ev.title}</div>
                            {!selectedDay && <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{ev.date}</div>}
                        </div>
                    ))}
                    {!loading && selectedDay && selectedEvents.length === 0 && (
                        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '24px 0', fontSize: '14px' }}>No events on this day</div>
                    )}
                </SectionCard>
            </div>
        </DashboardGrid>
    );
}
