import Sidebar from "../components/admin/Sidebar";
import Topbar from "../components/admin/Topbar";

import AdminRoutes from "../routes/AdminRoutes";

import useSidebar from "../hooks/useSidebar";

import "../styles/admin/layout.css";
import "../styles/admin/responsive.css";

export default function AdminLayout() {

    const { collapsed } = useSidebar();

    return (

        <div className="admin-layout">

            <Sidebar />

            <section
                className={`admin-main ${collapsed ? "collapsed" : ""}`}
            >

                <Topbar />

                <main className="admin-content">

                    <AdminRoutes />

                </main>

            </section>

        </div>

    );

}