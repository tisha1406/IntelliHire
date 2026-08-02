import { useState, useMemo, useEffect } from "react";

import {
    ChevronLeft,
    ChevronRight,
    ArrowDownAZ,
    ArrowUpZA,
    ArrowUpDown,
} from "lucide-react";

import SearchBar from "./SearchBar";
import Skeleton from "./Skeleton";

import "./../../styles/admin/datatable.css";

export default function DataTable({

    columns = [],

    data = [],

    keyField = "id",

    pagination = true,

    rowsPerPage = 10,

    searchable = false,

    loading = false,

    className = "",

    emptyState = null,

    onSort = null,

    sortKey = null,

    sortDirection = null,

    onRowClick,

    emptyMessage = "No records found",

}) {

    const [currentPage, setCurrentPage] = useState(1);

    const [searchTerm, setSearchTerm] = useState("");

    const [sortConfig, setSortConfig] = useState({

        key: null,

        direction: null,

    });

    // ============================
    // Sorting
    // ============================

    const handleSort = (key) => {

        // External sorting (server side)

        if (onSort) {

            const nextDirection =

                sortKey === key &&

                sortDirection === "asc"

                    ? "desc"

                    : "asc";

            onSort(

                key,

                nextDirection

            );

            return;

        }

        // Internal sorting

        let direction = "ascending";

        if (

            sortConfig.key === key &&

            sortConfig.direction === "ascending"

        ) {

            direction = "descending";

        }

        setSortConfig({

            key,

            direction,

        });

    };

    // ============================
    // Search Filter
    // ============================

    const filteredData = useMemo(() => {

        if (!searchTerm)

            return data;

        const lowerSearch =

            searchTerm.toLowerCase();

        return data.filter((row) =>

            columns.some((col) => {

                const field =

                    col.key ||

                    col.dataIndex;

                if (!field)

                    return false;

                const value =

                    row[field];

                if (

                    value === null ||

                    value === undefined

                )

                    return false;

                return String(value)

                    .toLowerCase()

                    .includes(lowerSearch);

            })

        );

    }, [

        data,

        searchTerm,

        columns,

    ]);

    // ============================
    // Internal Sort
    // ============================

    const sortedData = useMemo(() => {

        if (onSort)

            return filteredData;

        return [

            ...filteredData,

        ].sort((a, b) => {

            if (!sortConfig.key)

                return 0;

            const valA =

                a[sortConfig.key];

            const valB =

                b[sortConfig.key];

            if (valA < valB) {
                return sortConfig.direction === "ascending" ? -1 : 1;
            }

            if (valA > valB) {
                return sortConfig.direction === "ascending" ? 1 : -1;
            }

            return 0;

        });

    }, [

        filteredData,

        sortConfig,

        onSort,

    ]);

    // ============================
    // Pagination
    // ============================

    const totalPages =

        Math.ceil(

            sortedData.length /

                rowsPerPage

        ) || 1;

    const paginatedData =

        pagination

            ? sortedData.slice(

                  (currentPage - 1) *

                      rowsPerPage,

                  currentPage *

                      rowsPerPage

              )

            : sortedData;

    // Reset page when search changes

    useEffect(() => {

        setCurrentPage(1);

    }, [searchTerm]);

    return (

        <div className={`datatable-container ${className}`}>

            {searchable && (

                <div className="datatable-toolbar">

                    <SearchBar

                        value={searchTerm}

                        onChange={setSearchTerm}

                        onClear={() => setSearchTerm("")}

                        placeholder="Search records..."

                    />

                </div>

            )}

            <div className="datatable-wrapper">

                <table className="datatable">

                    <thead>

                        <tr>

                            {columns.map((col, index) => {

                                const columnKey =
                                    col.key || col.dataIndex;

                                const isSorted =
                                    sortKey
                                        ? sortKey === columnKey
                                        : sortConfig.key === columnKey;

                                const direction =
                                    sortKey
                                        ? sortDirection
                                        : sortConfig.direction;

                                return (

                                    <th

                                        key={index}

                                        style={{

                                            width:
                                                col.width ||
                                                "auto",

                                            textAlign:
                                                col.align ||
                                                "left",

                                        }}

                                        className={
                                            col.sortable
                                                ? "sortable"
                                                : ""
                                        }

                                        onClick={() =>

                                            col.sortable &&
                                            handleSort(
                                                columnKey
                                            )

                                        }

                                    >

                                        <div

                                            className="th-content"

                                            style={{

                                                justifyContent:

                                                    col.align ===
                                                    "right"

                                                        ? "flex-end"

                                                        : col.align ===
                                                          "center"

                                                        ? "center"

                                                        : "flex-start",

                                            }}

                                        >

                                            {col.title ||
                                                col.label}

                                            {col.sortable && (

                                                <span className="sort-icon">

                                                    {isSorted ? (

                                                        direction ===
                                                        "ascending" ||

                                                        direction ===
                                                            "asc"

                                                            ? (

                                                                  <ArrowDownAZ
                                                                      size={
                                                                          14
                                                                      }
                                                                  />

                                                              )

                                                            : (

                                                                  <ArrowUpZA
                                                                      size={
                                                                          14
                                                                      }
                                                                  />

                                                              )

                                                    ) : (

                                                        <ArrowUpDown

                                                            size={14}

                                                            className="opacity-50"

                                                        />

                                                    )}

                                                </span>

                                            )}

                                        </div>

                                    </th>

                                );

                            })}

                        </tr>

                    </thead>

                    <tbody>

                        {loading ? (

                            Array.from({

                                length: rowsPerPage,

                            }).map((_, rowIndex) => (

                                <tr key={rowIndex}>

                                    {columns.map(

                                        (
                                            col,
                                            colIndex
                                        ) => (

                                            <td
                                                key={
                                                    colIndex
                                                }
                                            >

                                                <Skeleton

                                                    width="85%"

                                                    height="18px"

                                                />

                                            </td>

                                        )

                                    )}

                                </tr>

                            ))

                        ) : paginatedData.length >

                          0 ? (

                            paginatedData.map(

                                (

                                    row,

                                    rowIndex

                                ) => (

                                    <tr

                                        key={
                                            row[
                                                keyField
                                            ] ||
                                            rowIndex
                                        }

                                        onClick={() =>

                                            onRowClick &&
                                            onRowClick(
                                                row
                                            )

                                        }

                                        className={

                                            onRowClick

                                                ? "clickable-row"

                                                : ""

                                        }

                                    >

                                        {columns.map(

                                            (

                                                col,

                                                colIndex

                                            ) => {

                                                const field =
                                                    col.key ||
                                                    col.dataIndex;

                                                return (

                                                    <td

                                                        key={
                                                            colIndex
                                                        }

                                                        style={{

                                                            textAlign:

                                                                col.align ||

                                                                "left",

                                                        }}

                                                    >

                                                        {col.render

                                                            ? col.render(

                                                                  row[
                                                                      field
                                                                  ],

                                                                  row

                                                              )

                                                            : row[
                                                                  field
                                                              ]}

                                                    </td>

                                                );

                                            }

                                        )}

                                    </tr>

                                )

                            )

                        ) : (

                            <tr>

                                <td

                                    colSpan={
                                        columns.length
                                    }

                                    className="empty-cell"

                                >

                                    {emptyState || (

                                        <div className="empty-state-simple">

                                            {emptyMessage}

                                        </div>

                                    )}

                                </td>

                            </tr>

                        )}

                    </tbody>

                </table>

            </div>

                        {pagination && totalPages > 1 && (
                <div className="datatable-footer">
                    <span className="pagination-info">
                        Showing {(currentPage - 1) * rowsPerPage + (sortedData.length ? 1 : 0)}
                        {" "}to{" "}
                        {Math.min(currentPage * rowsPerPage, sortedData.length)}
                        {" "}of {sortedData.length} entries
                    </span>

                    <div className="pagination-controls">
                        <button
                            className="page-btn"
                            disabled={currentPage === 1}
                            onClick={() =>
                                setCurrentPage((p) => Math.max(1, p - 1))
                            }
                        >
                            <ChevronLeft size={16} />
                        </button>

                        <span className="page-current">
                            Page {currentPage} of {totalPages}
                        </span>

                        <button
                            className="page-btn"
                            disabled={currentPage === totalPages}
                            onClick={() =>
                                setCurrentPage((p) =>
                                    Math.min(totalPages, p + 1)
                                )
                            }
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}