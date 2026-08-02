import { useParams } from "react-router-dom";
import CompanyWizard from "../../components/admin/CompanyWizard/index.jsx";

export default function EditCompany() {
    const { companyId } = useParams();
    
    return <CompanyWizard companyId={companyId} />;
}
