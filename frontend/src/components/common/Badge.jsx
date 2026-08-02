import "./../../styles/admin/badge.css";

export default function Badge({

    children,

    variant = "primary"

}) {

    return (

        <span className={`ih-badge ${variant}`}>

            {children}

        </span>

    );

}