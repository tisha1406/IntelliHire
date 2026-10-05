import { useParams } from "react-router-dom";
import StrategyForm from "../../components/admin/StrategyForm/index.jsx";

export default function EditStrategy() {
    const { strategyId } = useParams();
    return <StrategyForm strategyId={strategyId} />;
}
