import { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import './Select.css';

export interface SelectOption {
    value: string;
    label: string;
    group?: string;
}

interface SelectProps {
    id?: string;
    value: string;
    options: SelectOption[];
    onChange: (value: string) => void;
    placeholder?: string;
    'aria-label'?: string;
}

const Select = ({ id, value, options, onChange, placeholder, 'aria-label': ariaLabel }: SelectProps) => {
    const [open, setOpen] = useState(false);
    const [focusIdx, setFocusIdx] = useState(-1);
    const containerRef = useRef<HTMLDivElement>(null);
    const listRef = useRef<HTMLUListElement>(null);

    const selected = options.find(o => o.value === value);

    const groups = options.reduce<{ group: string; items: SelectOption[] }[]>((acc, opt) => {
        const g = opt.group || '';
        const existing = acc.find(a => a.group === g);
        if (existing) existing.items.push(opt);
        else acc.push({ group: g, items: [opt] });
        return acc;
    }, []);

    useEffect(() => {
        if (!open) return;
        const handler = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [open]);

    useEffect(() => {
        if (open && focusIdx >= 0 && listRef.current) {
            const item = listRef.current.children[focusIdx] as HTMLElement | undefined;
            item?.scrollIntoView({ block: 'nearest' });
        }
    }, [focusIdx, open]);

    const flatOptions = options;

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            setOpen(false);
            return;
        }
        if (!open && (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown')) {
            e.preventDefault();
            setOpen(true);
            const currentIdx = flatOptions.findIndex(o => o.value === value);
            setFocusIdx(currentIdx >= 0 ? currentIdx : 0);
            return;
        }
        if (!open) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setFocusIdx(prev => Math.min(prev + 1, flatOptions.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setFocusIdx(prev => Math.max(prev - 1, 0));
        } else if (e.key === 'Home') {
            e.preventDefault();
            setFocusIdx(0);
        } else if (e.key === 'End') {
            e.preventDefault();
            setFocusIdx(flatOptions.length - 1);
        } else if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (focusIdx >= 0 && focusIdx < flatOptions.length) {
                onChange(flatOptions[focusIdx].value);
                setOpen(false);
            }
        }
    };

    const handleToggle = () => {
        setOpen(prev => !prev);
        if (!open) {
            const currentIdx = flatOptions.findIndex(o => o.value === value);
            setFocusIdx(currentIdx >= 0 ? currentIdx : 0);
        }
    };

    const handleSelect = (opt: SelectOption) => {
        onChange(opt.value);
        setOpen(false);
    };

    let itemIndex = 0;

    return (
        <div className="custom-select" ref={containerRef}>
            <button
                type="button"
                id={id}
                className={`custom-select-trigger ${open ? 'open' : ''}`}
                onClick={handleToggle}
                onKeyDown={handleKeyDown}
                role="combobox"
                aria-expanded={open}
                aria-haspopup="listbox"
                aria-label={ariaLabel}
                aria-activedescendant={open && focusIdx >= 0 ? `${id}-opt-${focusIdx}` : undefined}
            >
                <span className={selected ? '' : 'custom-select-placeholder'}>
                    {selected ? selected.label : (placeholder || 'Select...')}
                </span>
                <ChevronDown size={16} className={`custom-select-chevron ${open ? 'rotated' : ''}`} aria-hidden="true" />
            </button>

            {open && (
                <ul
                    ref={listRef}
                    className="custom-select-menu"
                    role="listbox"
                    aria-labelledby={id}
                >
                    {groups.map((g) => {
                        const elems = [];
                        if (g.group) {
                            elems.push(
                                <li key={`grp-${g.group}`} className="custom-select-group" role="presentation">
                                    {g.group}
                                </li>
                            );
                        }
                        for (const opt of g.items) {
                            const idx = itemIndex++;
                            const isSelected = opt.value === value;
                            const isFocused = idx === focusIdx;
                            elems.push(
                                <li
                                    key={opt.value}
                                    id={`${id}-opt-${idx}`}
                                    role="option"
                                    aria-selected={isSelected}
                                    className={`custom-select-option ${isSelected ? 'selected' : ''} ${isFocused ? 'focused' : ''}`}
                                    onMouseEnter={() => setFocusIdx(idx)}
                                    onMouseDown={(e) => { e.preventDefault(); handleSelect(opt); }}
                                >
                                    {opt.label}
                                </li>
                            );
                        }
                        return elems;
                    })}
                </ul>
            )}
        </div>
    );
};

export default Select;
