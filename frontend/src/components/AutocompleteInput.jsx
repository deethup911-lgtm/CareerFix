import React, { useState, useEffect, useRef } from 'react';

export default function AutocompleteInput({ 
  value, 
  onChange, 
  placeholder, 
  mode = "local", // "local" or "api"
  localSuggestions = [], // Array of strings for "local" mode
  className = ""
}) {
  const [query, setQuery] = useState(value || "");
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // KEY FIX: Track whether the user has actually typed something.
  // This prevents the API from firing on page load or value syncs.
  const userTyped = useRef(false);
  const wrapperRef = useRef(null);

  // Sync external value changes (e.g. when parent sets default values)
  // BUT do NOT trigger a search — only the user typing should do that.
  useEffect(() => {
    setQuery(value || "");
  }, [value]);

  // Handle outside click to close the dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced suggestion logic — only runs after the USER has typed
  useEffect(() => {
    if (!userTyped.current) return; // Don't fire on mount or external value sync

    if (mode === "local") {
      if (query.trim() === "") {
        setSuggestions(localSuggestions.slice(0, 5));
      } else {
        const filtered = localSuggestions.filter(s =>
          s.toLowerCase().includes(query.toLowerCase())
        );
        setSuggestions(filtered.slice(0, 5));
      }
      return;
    }

    // API Mode (GeoDB) — only trigger if user typed at least 2 characters
    if (query.trim().length < 2) {
      setSuggestions([]);
      setLoading(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/locations/autocomplete?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        setSuggestions(data.data || []);
        if (data.data?.length > 0) setIsOpen(true);
      } catch (e) {
        console.error("GeoDB fetch error:", e);
      } finally {
        setLoading(false);
      }
    }, 500); // 500ms debounce — generous to protect your RapidAPI quota

    return () => clearTimeout(timer);
  }, [query, mode, localSuggestions]);

  const handleChange = (e) => {
    userTyped.current = true; // Mark that the user has actively typed
    const val = e.target.value;
    setQuery(val);
    onChange(val);
    setIsOpen(true);
  };

  // When user focuses, only show dropdown if they've already typed something
  const handleFocus = () => {
    if (userTyped.current && suggestions.length > 0) {
      setIsOpen(true);
    }
  };

  const handleSelect = (suggestion) => {
    userTyped.current = false; // Reset so selecting doesn't re-trigger a search
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
        placeholder={placeholder}
        autoComplete="off"
      />
      
      {isOpen && (suggestions.length > 0 || loading) && (
        <ul style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: 'var(--card-bg, #1e2530)',
          border: '1px solid var(--border-color, #333)',
          borderRadius: '6px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          zIndex: 100,
          maxHeight: '200px',
          overflowY: 'auto',
          listStyle: 'none',
          padding: '0.25rem 0',
          margin: '0.25rem 0 0 0'
        }}>
          {loading && (
            <li style={{ padding: '0.5rem 1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Searching cities...
            </li>
          )}
          {!loading && suggestions.map((s, idx) => (
            <li 
              key={idx}
              onMouseDown={(e) => {
                e.preventDefault(); // Prevent input blur before click registers
                handleSelect(s);
              }}
              style={{
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                fontSize: '0.9rem',
                borderBottom: idx === suggestions.length - 1 ? 'none' : '1px solid var(--border-color, #333)',
                transition: 'background 0.15s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.07)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
