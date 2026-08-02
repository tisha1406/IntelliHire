import { useState, useEffect } from "react";
import { useAdminProfile } from "../../hooks/useAdminProfile";
import Card from "../../components/common/Card";

export default function AdminProfile() {
    const { data: profile, isLoading, updateProfile, isUpdating } = useAdminProfile();
    const [formData, setFormData] = useState({ name: "", email: "" });

    useEffect(() => {
        if (profile) {
            setFormData({ name: profile.name || "", email: profile.email || "" });
        }
    }, [profile]);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        updateProfile(formData);
    };

    if (isLoading) {
        return (
            <div className="admin-page">
                <div className="admin-page-header">
                    <h2>Admin Profile</h2>
                </div>
                <div>Loading profile...</div>
            </div>
        );
    }

    return (
        <div className="admin-page">
            <div className="admin-page-header">
                <h2>Admin Profile</h2>
                <p>Manage your personal information</p>
            </div>
            
            <div style={{ maxWidth: 600 }}>
                <Card title="Personal Information">
                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '16px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontWeight: 500 }}>Name</label>
                            <input 
                                type="text" 
                                name="name" 
                                value={formData.name} 
                                onChange={handleChange} 
                                style={{ padding: '10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                                required
                            />
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ fontWeight: 500 }}>Email Address</label>
                            <input 
                                type="email" 
                                name="email" 
                                value={formData.email} 
                                onChange={handleChange} 
                                style={{ padding: '10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                                required
                            />
                        </div>
                        <div style={{ marginTop: '8px' }}>
                            <button 
                                type="submit" 
                                disabled={isUpdating}
                                style={{ 
                                    padding: '10px 20px', 
                                    borderRadius: '6px', 
                                    background: 'var(--primary)', 
                                    color: 'white', 
                                    border: 'none', 
                                    cursor: isUpdating ? 'not-allowed' : 'pointer',
                                    fontWeight: 500
                                }}
                            >
                                {isUpdating ? "Saving..." : "Save Changes"}
                            </button>
                        </div>
                    </form>
                </Card>
            </div>
        </div>
    );
}
