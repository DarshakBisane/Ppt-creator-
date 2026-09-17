import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { App } from '@/App';
import { StudioPage } from '@/pages/StudioPage';
import { ReferenceUploader } from '@/components/studio/ReferenceUploader';

describe('Presentation Studio & UI Navigation Tests', () => {
  it('renders landing page with primary value proposition and CTAs', () => {
    render(<App />);
    expect(screen.getByText(/Create better presentations/i)).toBeInTheDocument();
    expect(screen.getByText(/Create from Topic/i)).toBeInTheDocument();
    expect(screen.getByText(/Use Reference PPT/i)).toBeInTheDocument();
  });

  it('navigates from landing to studio when clicking Create from Topic CTA', () => {
    render(<App />);
    const cta = screen.getByRole('button', { name: /Create from Topic/i });
    fireEvent.click(cta);
    expect(screen.getByRole('heading', { level: 1, name: /Presentation Studio/i })).toBeInTheDocument();
  });

  it('switches between Topic Mode and Reference PPT Mode', () => {
    render(<StudioPage initialMode="topic" />);
    expect(screen.getByText(/Presentation Topic & Prompt/i)).toBeInTheDocument();

    // Switch to Reference Mode
    const refModeBtn = screen.getByRole('button', { name: /From Reference PPT/i });
    fireEvent.click(refModeBtn);
    expect(screen.getByText(/Upload Reference PowerPoint/i)).toBeInTheDocument();
    expect(screen.getByText(/New Presentation Topic/i)).toBeInTheDocument();

    // Switch back to Topic Mode
    const topicModeBtn = screen.getByRole('button', { name: /Create from Topic/i });
    fireEvent.click(topicModeBtn);
    expect(screen.getByText(/Presentation Topic & Prompt/i)).toBeInTheDocument();
  });

  it('updates topic input value and character count', () => {
    render(<StudioPage initialMode="topic" />);
    const textarea = screen.getByPlaceholderText(/Describe your presentation topic/i);
    fireEvent.change(textarea, { target: { value: 'Quantum Computing Fundamentals' } });
    expect(textarea).toHaveValue('Quantum Computing Fundamentals');
    expect(screen.getByText(/30 characters/i)).toBeInTheDocument();
  });

  it('validates empty topic on submission and displays error', () => {
    render(<StudioPage initialMode="topic" />);
    const generateBtn = screen.getByRole('button', { name: /Generate Presentation/i });
    fireEvent.click(generateBtn);
    const errorMessages = screen.getAllByText(/Please enter a presentation topic to proceed/i);
    expect(errorMessages.length).toBeGreaterThanOrEqual(1);
  });

  it('requires reference file in reference mode on submission', () => {
    render(<StudioPage initialMode="reference" />);
    const topicInput = screen.getByPlaceholderText(/What should the new presentation be about/i);
    fireEvent.change(topicInput, { target: { value: 'AI Governance' } });

    const generateBtn = screen.getByRole('button', { name: /Generate Presentation/i });
    fireEvent.click(generateBtn);
    expect(screen.getByText(/Please upload a reference PowerPoint \(\.pptx\) file/i)).toBeInTheDocument();
  });

  it('rejects invalid non-pptx files in ReferenceUploader', () => {
    const onFileSelect = (file: File | null) => file;
    const { container } = render(
      <ReferenceUploader
        file={null}
        onFileSelect={onFileSelect}
        topic=""
        onTopicChange={() => {}}
      />
    );

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const fakePdf = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [fakePdf] } });
    expect(screen.getByText(/Only PowerPoint \.pptx files are supported/i)).toBeInTheDocument();
  });

  it('rejects files exceeding 25 MB in ReferenceUploader', () => {
    const onFileSelect = (file: File | null) => file;
    const { container } = render(
      <ReferenceUploader
        file={null}
        onFileSelect={onFileSelect}
        topic=""
        onTopicChange={() => {}}
      />
    );

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const oversizedFile = new File(['a'.repeat(1024)], 'huge.pptx', {
      type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    });
    Object.defineProperty(oversizedFile, 'size', { value: 26 * 1024 * 1024 });

    fireEvent.change(input, { target: { files: [oversizedFile] } });
    expect(screen.getByText(/File size exceeds the 25 MB limit/i)).toBeInTheDocument();
  });

  it('submits form successfully and transitions to pipeline tab', () => {
    render(<StudioPage initialMode="topic" />);
    const textarea = screen.getByPlaceholderText(/Describe your presentation topic/i);
    fireEvent.change(textarea, { target: { value: 'Autonomous Systems Architecture' } });

    const generateBtn = screen.getByRole('button', { name: /Generate Presentation/i });
    fireEvent.click(generateBtn);

    expect(screen.getByText(/Generation Pipeline/i)).toBeInTheDocument();
  });

  it('resets form state when clicking reset button', () => {
    render(<StudioPage initialMode="topic" />);
    const textarea = screen.getByPlaceholderText(/Describe your presentation topic/i);
    fireEvent.change(textarea, { target: { value: 'Text to be reset' } });
    expect(textarea).toHaveValue('Text to be reset');

    const resetBtn = screen.getByRole('button', { name: /Reset Form/i });
    fireEvent.click(resetBtn);
    expect(textarea).toHaveValue('');
  });
});
