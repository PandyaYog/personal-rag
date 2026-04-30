import { useEffect, useRef, useCallback } from 'react';
import { AlertTriangle } from 'lucide-react';
import './ConfirmModal.css';

interface ConfirmModalProps {
    open: boolean;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    variant?: 'danger' | 'default';
    loading?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

const ConfirmModal = ({
    open,
    title,
    message,
    confirmLabel = 'Delete',
    cancelLabel = 'Cancel',
    variant = 'danger',
    loading = false,
    onConfirm,
    onCancel,
}: ConfirmModalProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const cancelRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        if (open) {
            cancelRef.current?.focus();
            document.body.style.overflow = 'hidden';
        }
        return () => { document.body.style.overflow = ''; };
    }, [open]);

    const handleKeyDown = useCallback((e: KeyboardEvent) => {
        if (e.key === 'Escape') {
            onCancel();
            return;
        }
        if (e.key === 'Tab' && dialogRef.current) {
            const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
                'button:not([disabled]), [href], input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
            );
            if (focusable.length === 0) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];

            if (e.shiftKey) {
                if (document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                }
            } else {
                if (document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        }
    }, [onCancel]);

    useEffect(() => {
        if (!open) return;
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [open, handleKeyDown]);

    if (!open) return null;

    return (
        <div className="cm-overlay" onClick={onCancel}>
            <div
                ref={dialogRef}
                className="cm-dialog"
                role="alertdialog"
                aria-modal="true"
                aria-labelledby="cm-title"
                aria-describedby="cm-message"
                onClick={(e) => e.stopPropagation()}
            >
                <div className={`cm-icon-wrap cm-icon-${variant}`} aria-hidden="true">
                    <AlertTriangle size={22} />
                </div>
                <h2 id="cm-title" className="cm-title">{title}</h2>
                <p id="cm-message" className="cm-message">{message}</p>
                <div className="cm-actions">
                    <button
                        ref={cancelRef}
                        className="cm-btn cm-btn-cancel"
                        onClick={onCancel}
                        disabled={loading}
                    >
                        {cancelLabel}
                    </button>
                    <button
                        className={`cm-btn cm-btn-confirm cm-btn-${variant}`}
                        onClick={onConfirm}
                        disabled={loading}
                    >
                        {loading ? 'Deleting...' : confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmModal;
