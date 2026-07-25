import React, { useState } from 'react';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

interface PasswordInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  showStrength?: boolean;
}

export const PasswordInput: React.FC<PasswordInputProps> = ({
  label,
  error,
  showStrength = false,
  value,
  className = '',
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const passwordStr = String(value || '');

  // Calculate password strength
  const hasMinLength = passwordStr.length >= 8;
  const hasUpper = /[A-Z]/.test(passwordStr);
  const hasLower = /[a-z]/.test(passwordStr);
  const hasNumber = /[0-9]/.test(passwordStr);
  const hasSpecial = /[^A-Za-z0-9]/.test(passwordStr);

  const score = [hasMinLength, hasUpper, hasLower, hasNumber, hasSpecial].filter(Boolean).length;

  const getStrengthLabel = () => {
    if (passwordStr.length === 0) return { text: '', color: 'bg-transparent', width: 'w-0' };
    if (score <= 2) return { text: 'Weak', color: 'bg-red-500', width: 'w-1/4' };
    if (score === 3) return { text: 'Fair', color: 'bg-amber-500', width: 'w-2/4' };
    if (score === 4) return { text: 'Good', color: 'bg-blue-500', width: 'w-3/4' };
    return { text: 'Strong', color: 'bg-emerald-500', width: 'w-full' };
  };

  const strength = getStrengthLabel();

  return (
    <div className="space-y-1 text-left">
      {label && (
        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider">
          {label}
        </label>
      )}

      <div className="relative">
        <input
          {...props}
          type={showPassword ? 'text' : 'password'}
          value={value}
          className={`input pr-10 ${error ? 'border-red-500 focus:border-red-500' : ''} ${className}`}
        />
        <button
          type="button"
          tabIndex={0}
          aria-label={showPassword ? 'Hide password' : 'Show password'}
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white focus:outline-none focus:text-white transition-colors p-1"
        >
          {showPassword ? (
            <EyeSlashIcon className="w-5 h-5" />
          ) : (
            <EyeIcon className="w-5 h-5" />
          )}
        </button>
      </div>

      {error && <p className="text-xs text-red-400 font-medium">{error}</p>}

      {showStrength && passwordStr.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <div className="h-1.5 w-full bg-[var(--color-surface-2)] rounded-full overflow-hidden">
            <div className={`h-full ${strength.color} ${strength.width} transition-all duration-300`} />
          </div>
          <div className="flex justify-between items-center text-[11px] text-gray-400">
            <span>Strength: <span className="font-bold text-gray-200">{strength.text}</span></span>
            <div className="flex gap-2">
              <span className={hasMinLength ? 'text-emerald-400' : 'text-gray-500'}>8+ chars</span>
              <span className={hasUpper ? 'text-emerald-400' : 'text-gray-500'}>A-Z</span>
              <span className={hasLower ? 'text-emerald-400' : 'text-gray-500'}>a-z</span>
              <span className={hasNumber ? 'text-emerald-400' : 'text-gray-500'}>0-9</span>
              <span className={hasSpecial ? 'text-emerald-400' : 'text-gray-500'}>Symbol</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
