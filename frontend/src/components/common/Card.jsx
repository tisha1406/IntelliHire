import "./../../styles/admin/cards.css";

export default function Card({

    children,

    className = "",

    title,

    subtitle,

    footer

}) {

    return (

        <div className={`ih-card ${className}`}>

            {(title || subtitle) && (

                <div className="ih-card-header">

                    {title &&

                        <h3>{title}</h3>

                    }

                    {subtitle &&

                        <p>{subtitle}</p>

                    }

                </div>

            )}

            <div className="ih-card-body">

                {children}

            </div>

            {footer &&

                <div className="ih-card-footer">

                    {footer}

                </div>

            }

        </div>

    );

}