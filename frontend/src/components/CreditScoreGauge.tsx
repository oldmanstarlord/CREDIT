import React, { useEffect, useState, useRef } from 'react';

interface CreditScoreGaugeProps {
  score: number;
  maxScore?: number;
  minScore?: number;
  size?: number;
  animated?: boolean;
}

const getRiskBand = (score: number): { label: string; color: string; bgColor: string } => {
  if (score >= 750) return { label: 'LOW RISK', color: '#10B981', bgColor: '#D1FAE5' };
  if (score >= 650) return { label: 'MEDIUM RISK', color: '#F59E0B', bgColor: '#FEF3C7' };
  if (score >= 550) return { label: 'HIGH RISK', color: '#F97316', bgColor: '#FFEDD5' };
  return { label: 'VERY HIGH RISK', color: '#EF4444', bgColor: '#FEE2E2' };
};

const CreditScoreGauge: React.FC<CreditScoreGaugeProps> = ({
  score,
  maxScore = 850,
  minScore = 300,
  size = 280,
  animated = true,
}) => {
  const [displayScore, setDisplayScore] = useState(animated ? 0 : score);
  const [fillProgress, setFillProgress] = useState(animated ? 0 : 1);
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);

  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const sweepAngle = 240;
  const arcLength = circumference * (sweepAngle / 360);
  const scorePercent = Math.max(0, Math.min(1, (score - minScore) / (maxScore - minScore)));
  const strokeDashoffset = arcLength * (1 - scorePercent * fillProgress);
  const band = getRiskBand(score);

  useEffect(() => {
    if (!animated) {
      setDisplayScore(score);
      setFillProgress(1);
      return;
    }
    const duration = 1500;
    startTimeRef.current = null;

    const animate = (timestamp: number) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);

      setDisplayScore(Math.round(eased * score));
      setFillProgress(eased);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [score, animated]);

  const startAngle = -210;
  const gradientColors = [
    { offset: '0%', color: '#EF4444' },
    { offset: '30%', color: '#F97316' },
    { offset: '55%', color: '#F59E0B' },
    { offset: '100%', color: '#10B981' },
  ];

  return (
    <div className="flex flex-col items-center" role="img" aria-label={`Credit score: ${score} out of ${maxScore}, ${band.label}`}>
      <svg width={size} height={size * 0.75} viewBox="-100 -100 200 160">
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="100%" x2="100%" y2="0%">
            {gradientColors.map((c) => (
              <stop key={c.offset} offset={c.offset} stopColor={c.color} />
            ))}
          </linearGradient>
          <filter id="scoreGlow">
            <feDropShadow dx="0" dy="0" stdDeviation="8" floodColor={band.color} floodOpacity="0.4" />
          </filter>
        </defs>

        {/* Background track */}
        <circle
          cx="0" cy="0" r={radius}
          fill="none" stroke="#E2E8F0" strokeWidth="12"
          strokeDasharray={`${arcLength} ${circumference - arcLength}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform={`rotate(${startAngle})`}
        />

        {/* Filled arc */}
        <circle
          cx="0" cy="0" r={radius}
          fill="none" stroke="url(#gaugeGradient)" strokeWidth="12"
          strokeDasharray={`${arcLength} ${circumference - arcLength}`}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform={`rotate(${startAngle})`}
          filter="url(#scoreGlow)"
          style={{ transition: animated ? 'none' : 'stroke-dashoffset 0.4s ease' }}
        />

        {/* Score number */}
        <text
          x="0" y="-8"
          textAnchor="middle"
          fill={band.color}
          fontSize="42"
          fontFamily="'Clash Display', serif"
          fontWeight="700"
          letterSpacing="-0.04em"
        >
          {displayScore}
        </text>

        {/* "out of 850" label */}
        <text x="0" y="16" textAnchor="middle" fill="#64748B" fontSize="11" fontFamily="'Instrument Sans', sans-serif">
          out of {maxScore}
        </text>

        {/* Risk band label */}
        <g transform="translate(0, 42)">
          <rect x="-40" y="-10" width="80" height="20" rx="10" fill={band.bgColor} />
          <text x="0" y="4" textAnchor="middle" fill={band.color} fontSize="9" fontWeight="600" fontFamily="'Instrument Sans', sans-serif">
            {band.label}
          </text>
        </g>
      </svg>
    </div>
  );
};

export default CreditScoreGauge;
