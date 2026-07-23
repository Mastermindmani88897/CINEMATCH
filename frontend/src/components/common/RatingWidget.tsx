import React, { useState } from 'react';
import { StarIcon } from '@heroicons/react/24/solid';

interface RatingWidgetProps {
  initialRating?: number;
  onRate: (rating: number) => void;
  disabled?: boolean;
}

export const RatingWidget: React.FC<RatingWidgetProps> = ({
  initialRating = 0,
  onRate,
  disabled = false,
}) => {
  const [hoverRating, setHoverRating] = useState<number | null>(null);

  const displayRating = hoverRating !== null ? hoverRating : initialRating;

  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={disabled}
          onMouseEnter={() => !disabled && setHoverRating(star)}
          onMouseLeave={() => !disabled && setHoverRating(null)}
          onClick={() => !disabled && onRate(star)}
          className={`p-1 transition-transform ${disabled ? 'cursor-default' : 'hover:scale-125 cursor-pointer'}`}
        >
          <StarIcon
            className={`w-6 h-6 ${
              star <= displayRating ? 'text-[var(--color-accent)]' : 'text-gray-600'
            }`}
          />
        </button>
      ))}
      <span className="ml-2 text-sm font-bold text-gray-300">
        {displayRating > 0 ? `${displayRating}.0 / 5` : 'Rate'}
      </span>
    </div>
  );
};
