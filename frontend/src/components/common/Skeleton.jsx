import "./../../styles/admin/skeleton.css";

export default function Skeleton({

    width = "100%",

    height = "20px"

}) {

    return (

        <div

            className="skeleton"

            style={{

                width,

                height

            }}

        />

    );

}