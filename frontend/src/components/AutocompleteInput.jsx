import React, { useState, useEffect, useRef, useCallback } from 'react';

export default function AutocompleteInput({ 
  value, 
  onChange, 
  placeholder, 
  mode = "local",
  localSuggestions = [],
  className = ""
}) {
  const [query, setQuery] = useState(value || "");
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // userTyped ref: ONLY true when the human physically presses a key.
  // This prevents the API from firing on mount, value syncs, or programmatic updates.
  const userTyped = useRef(false);
  const wrapperRef = useRef(null);

  // Sync external value (e.g. parent sets default "Remote" or "India")
  // without triggering any dropdown logic.
  useEffect(() => {
    setQuery(value || "");
  }, [value]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // KEY FIX: localSuggestions is a NEW array reference every render.
  // Storing it as a JSON string inside the dep array prevents infinite loops.
  const localSuggestionsKey = JSON.stringify(localSuggestions);

  useEffect(() => {
    // Only run if the user actually typed something
    if (!userTyped.current) return;

    if (mode === "local") {
      const q = query.trim().toLowerCase();
      const parsed = JSON.parse(localSuggestionsKey);
      const filtered = q === ""
        ? parsed.slice(0, 5)
        : parsed.filter(s => s.toLowerCase().includes(q)).slice(0, 5);
      setSuggestions(filtered);
      setIsOpen(filtered.length > 0);
      return;
    }

    // API mode (GeoDB Cities) — minimum 2 chars before firing
    if (query.trim().length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      setLoading(false);
      return;
    }

    // Debounce: wait 500ms after last keystroke
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `http://localhost:8000/api/locations/autocomplete?q=${encodeURIComponent(query.trim())}`
        );
        const data = await res.json();
        const cities = data.data || [];
        setSuggestions(cities);
        setIsOpen(cities.length > 0);
      } catch (e) {
        console.error("GeoDB fetch error:", e);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, mode, localSuggestionsKey]);

  const handleChange = (e) => {
    userTyped.current = true;
    const val = e.target.value;
    setQuery(val);
    onChange(val);
    // Show loading indicator immediately for API mode while debouncing
    if (mode === "api" && val.trim().length >= 2) {
      setIsOpen(true);
    }
  };

  const handleFocus = () => {
    // Only re-open if user had previously typed and suggestions exist
    if (userTyped.current && suggestions.length > 0) {
      setIsOpen(true);
    }
  };

  const handleBlur = () => {
    // Small delay so onMouseDown on suggestions fires first
    setTimeout(() => setIsOpen(false), 150);
  };

  const handleSelect = (suggestion) => {
    userTyped.current = false; // Reset so programmatic set doesn't re-trigger search
    setQuery(suggestion);
    onChange(suggestion);
    setIsOpen(false);
    setSuggestions([]);
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative', width: '100%' }}>
      <input
        type="text"
        className={className}
        value={query}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={placeholder}
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
      />

      {isOpen && (suggestions.length > 0 || loading) && (
        <ul
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            left: 0,
            right: 0,
            background: 'var(--card-bg, #1e2530)',
            border: '1px solid var(--border-color, #333)',
            borderRadius: '6px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.55)',
            zIndex: 999,
            maxHeight: '200px',
            overflowY: 'auto',
            listStyle: 'none',
            padding: '0.25rem 0',
            margin: 0,
          }}
        >
          {loading && (
            <li style={{ padding: '0.5rem 1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Searching cities...
            </li>
          )}
          {!loading && suggestions.map((s, idx) => (
            <li
              key={idx}
              onMouseDown={(e) => {
                e.preventDefault(); // Prevent blur from closing dropdown before selection
                handleSelect(s);
              }}
              style={{
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                fontSize: '0.9rem',
                borderBottom: idx < suggestions.length - 1
                  ? '1px solid var(--border-color, #333)'
                  : 'none',
                transition: 'background 0.12s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.07)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
