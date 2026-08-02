import Modal from "./Modal";
import Button from "./Button";
import { AlertTriangle } from "lucide-react";

export default function ConfirmDialog({
    isOpen,
    onClose,
    onConfirm,
    title = "Are you sure?",
    message = "This action cannot be undone.",
    confirmText = "Confirm",
    cancelText = "Cancel",
    type = "danger",
    isDestructive = true,
    isLoading = false,
    ...props
}) {

    return (

        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={title}
            size="sm"
            position="top-right"
            footer={
                <>
                    <Button
                        variant="outline"
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        {cancelText}
                    </Button>

                    <Button
                        variant={
                            isDestructive
                                ? "danger"
                                : type
                        }
                        onClick={onConfirm}
                        disabled={isLoading}
                    >
                        {isLoading
                            ? "Processing..."
                            : confirmText}
                    </Button>
                </>
            }
            {...props}
        >

            <div className="confirm-dialog-content">

                {isDestructive && (

                    <div className="confirm-dialog-icon">

                        <AlertTriangle size={22} />

                    </div>

                )}

                <p className="confirm-dialog-msg">

                    {message}

                </p>

            </div>

        </Modal>

    );

}