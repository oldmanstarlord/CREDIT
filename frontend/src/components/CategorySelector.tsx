import React from 'react';
import { Wheat, HardHat, Bike, Store, Heart, BadgeCheck } from 'lucide-react';

interface CategorySelectorProps {
  selected: string;
  onSelect: (category: string) => void;
}

const categories = [
  { id: 'farmer', label: 'Farmer', sublabel: 'Agricultural & land-based income', icon: Wheat, color: '#10B981' },
  { id: 'daily_wage_worker', label: 'Daily Worker', sublabel: 'Construction, labor, daily earnings', icon: HardHat, color: '#F59E0B' },
  { id: 'gig_worker', label: 'Gig Worker', sublabel: 'Platform-based delivery & rides', icon: Bike, color: '#00AEEF' },
  { id: 'msme_owner', label: 'MSME Owner', sublabel: 'Small business & shop owner', icon: Store, color: '#8B5CF6' },
  { id: 'homemaker', label: 'Homemaker', sublabel: 'Household-based, nominee required', icon: Heart, color: '#EC4899' },
  { id: 'low_income_salaried', label: 'Salaried', sublabel: 'Fixed monthly salary employment', icon: BadgeCheck, color: '#6366F1' },
];

const CategorySelector: React.FC<CategorySelectorProps> = ({ selected, onSelect }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {categories.map((cat, index) => {
        const isSelected = selected === cat.id;
        const Icon = cat.icon;
        return (
          <button
            key={cat.id}
            onClick={() => onSelect(cat.id)}
            className={`
              relative p-6 rounded-card border-2 text-left transition-all duration-300 ease-spring
              hover:-translate-y-0.5 hover:shadow-card-user
              ${isSelected
                ? 'border-barclays-navy bg-barclays-lightblue shadow-card-user'
                : 'border-user-border bg-user-surface hover:border-barclays-navy'
              }
            `}
            style={{ animationDelay: `${index * 60}ms` }}
            aria-pressed={isSelected}
          >
            {isSelected && (
              <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-barclays-navy flex items-center justify-center">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M3 7l3 3 5-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            )}
            <div
              className="w-14 h-14 rounded-xl flex items-center justify-center mb-3"
              style={{ backgroundColor: `${cat.color}15` }}
            >
              <Icon size={28} style={{ color: cat.color }} />
            </div>
            <h3 className="text-base font-semibold text-user-text font-body">{cat.label}</h3>
            <p className="text-xs text-user-muted mt-1 font-body">{cat.sublabel}</p>
          </button>
        );
      })}
    </div>
  );
};

export default CategorySelector;
