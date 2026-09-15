import React from 'react';
import { HeroSection } from '@/components/landing/HeroSection';
import { FeaturesGrid } from '@/components/landing/FeaturesGrid';
import { HowItWorks } from '@/components/landing/HowItWorks';
import { CreationMode } from '@/types';

interface LandingPageProps {
  onStartCreation: (mode: CreationMode) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onStartCreation }) => {
  return (
    <div className="space-y-4">
      <HeroSection onStartCreation={onStartCreation} />
      <FeaturesGrid />
      <HowItWorks />
    </div>
  );
};
