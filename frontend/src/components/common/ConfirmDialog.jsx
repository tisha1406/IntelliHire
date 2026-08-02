import React from "react";
import Modal from "./Modal";
import Button from "./Button";

export default function ConfirmDialog({
    isOpen,
    onClose,
    onConfirm,
    title = "Are you sure?",
    message = "This action cannot be undone.",
    confirmText = "Confirm",
    cancelText = "Cancel",
    type = "danger", // danger, warning, primary
    ...props
}) {
    return (
        <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm" position="top-right" {...props}>
            <div className="confirm-dialog-content">
                <p className="confirm-dialog-msg">{message}</p>
                <div className="confirm-dialog-actions">
                    <Button variant="ghost" onClick={onClose}>
                        {cancelText}
                    </Button>
                    <button
    onClick={() => {
        console.log("HTML Button");
        onConfirm();
    }}
>
    Confirm
</button>
                </div>
            </div>
        </Modal>
    );
}
