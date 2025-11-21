"""
Comprehensive Verification Suite - All 6 Verification Strategies
Ensures text quality through multiple validation approaches
"""

import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import json
from datetime import datetime
from difflib import SequenceMatcher
import random

from tagore_config import (
    CONSENSUS_VERIFICATION_CONFIG,
    CONFIDENCE_VERIFICATION_CONFIG,
    LANGUAGE_MODEL_VERIFICATION_CONFIG,
    HISTORICAL_VERIFICATION_CONFIG,
    MANUAL_VERIFICATION_CONFIG,
    DIFF_VISUALIZATION_CONFIG,
    HISTORICAL_EVENTS,
    KNOWN_CORRESPONDENTS,
    DOCUMENT_METADATA
)


class VerificationSuite:
    """
    Comprehensive text verification using 6 complementary strategies.
    Implements all 6 Verification Strategies (V1-V6)
    """

    def __init__(self):
        """Initialize verification suite."""
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self._init_language_model()
        self._init_ner()

        # Statistics tracking
        self.verification_stats = defaultdict(int)

    def _init_language_model(self):
        """Initialize language model for perplexity analysis."""
        self.language_model = None

        if LANGUAGE_MODEL_VERIFICATION_CONFIG['enabled']:
            try:
                from transformers import GPT2LMHeadModel, GPT2Tokenizer
                import torch

                model_name = LANGUAGE_MODEL_VERIFICATION_CONFIG['model_name']
                self.lm_tokenizer = GPT2Tokenizer.from_pretrained(model_name)
                self.lm_model = GPT2LMHeadModel.from_pretrained(model_name)
                self.lm_model.eval()

                self.logger.info(f"Language model loaded: {model_name}")

            except Exception as e:
                self.logger.warning(f"Failed to load language model: {e}")

    def _init_ner(self):
        """Initialize Named Entity Recognition."""
        self.ner_pipeline = None

        if LANGUAGE_MODEL_VERIFICATION_CONFIG['use_ner']:
            try:
                from transformers import pipeline

                self.ner_pipeline = pipeline("ner", grouped_entities=True)
                self.logger.info("NER pipeline initialized")

            except Exception as e:
                self.logger.warning(f"Failed to initialize NER: {e}")

    def verify_all(self, ocr_results: Dict, image_path: Path = None) -> Dict:
        """
        Run all verification strategies on OCR results.

        Args:
            ocr_results: Dictionary with OCR engine results and consensus
            image_path: Optional path to original image

        Returns:
            Comprehensive verification report
        """
        self.logger.info("Running comprehensive verification suite")

        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'image_path': str(image_path) if image_path else None,
            'verifications': {},
            'overall_quality': {},
            'flags': [],
            'recommendations': []
        }

        # V1: Cross-Engine Consensus Analysis
        if CONSENSUS_VERIFICATION_CONFIG['enabled']:
            consensus_report = self.verify_consensus(ocr_results)
            report['verifications']['consensus'] = consensus_report

            if consensus_report['agreement_score'] < CONSENSUS_VERIFICATION_CONFIG['agreement_threshold']:
                report['flags'].append({
                    'type': 'low_consensus',
                    'severity': 'high',
                    'message': f"Low consensus: {consensus_report['agreement_score']:.2f}"
                })

        # V2: Confidence Score Tracking
        if CONFIDENCE_VERIFICATION_CONFIG['enabled']:
            confidence_report = self.verify_confidence(ocr_results)
            report['verifications']['confidence'] = confidence_report

            if confidence_report['average_confidence'] < CONFIDENCE_VERIFICATION_CONFIG['thresholds']['good']:
                report['flags'].append({
                    'type': 'low_confidence',
                    'severity': 'medium',
                    'message': f"Low confidence: {confidence_report['average_confidence']:.2f}"
                })

        # V3: Language Model Validation
        if LANGUAGE_MODEL_VERIFICATION_CONFIG['enabled']:
            text = ocr_results['consensus']['text']
            lm_report = self.verify_language_model(text)
            report['verifications']['language_model'] = lm_report

            if lm_report['high_perplexity_sentences']:
                report['flags'].append({
                    'type': 'high_perplexity',
                    'severity': 'medium',
                    'message': f"{len(lm_report['high_perplexity_sentences'])} suspicious sentences detected"
                })

        # V4: Historical & Contextual Validation
        if HISTORICAL_VERIFICATION_CONFIG['enabled']:
            text = ocr_results['consensus']['text']
            historical_report = self.verify_historical_context(text)
            report['verifications']['historical'] = historical_report

            if historical_report['anomalies']:
                report['flags'].append({
                    'type': 'historical_anomaly',
                    'severity': 'low',
                    'message': f"{len(historical_report['anomalies'])} potential anachronisms"
                })

        # V5: Manual Sampling Requirements
        if MANUAL_VERIFICATION_CONFIG['enabled']:
            sampling_report = self.generate_sampling_plan(ocr_results)
            report['verifications']['sampling'] = sampling_report

        # V6: Diff Visualization Data
        if DIFF_VISUALIZATION_CONFIG['enabled']:
            diff_data = self.generate_diff_visualization(ocr_results)
            report['verifications']['diff_visualization'] = diff_data

        # Calculate overall quality score
        report['overall_quality'] = self._calculate_overall_quality(report)

        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)

        return report

    # ==================== V1: Cross-Engine Consensus ====================

    def verify_consensus(self, ocr_results: Dict) -> Dict:
        """
        Verification Strategy 1: Cross-Engine Consensus Analysis
        Compare outputs from all OCR engines.
        """
        engine_results = ocr_results.get('engine_results', {})

        if len(engine_results) < 2:
            return {
                'agreement_score': 0.0,
                'status': 'insufficient_engines',
                'disagreements': []
            }

        # Extract texts
        texts = {k: v['text'] for k, v in engine_results.items() if v['text']}

        if len(texts) < 2:
            return {
                'agreement_score': 0.0,
                'status': 'insufficient_results',
                'disagreements': []
            }

        # Calculate pairwise agreement
        agreements = []
        disagreements = []

        engines = list(texts.keys())

        for i in range(len(engines)):
            for j in range(i + 1, len(engines)):
                engine1, engine2 = engines[i], engines[j]
                text1, text2 = texts[engine1], texts[engine2]

                # Calculate similarity
                similarity = SequenceMatcher(None, text1, text2).ratio()
                agreements.append(similarity)

                # Find specific disagreements
                if similarity < 0.95:
                    disagreements.append({
                        'engines': [engine1, engine2],
                        'similarity': similarity,
                        'length_diff': abs(len(text1) - len(text2))
                    })

        avg_agreement = np.mean(agreements) if agreements else 0.0

        return {
            'agreement_score': avg_agreement,
            'pairwise_agreements': dict(zip(
                [f"{engines[i]}-{engines[j]}" for i in range(len(engines)) for j in range(i+1, len(engines))],
                agreements
            )),
            'disagreements': disagreements,
            'status': 'pass' if avg_agreement >= CONSENSUS_VERIFICATION_CONFIG['agreement_threshold'] else 'review_needed'
        }

    # ==================== V2: Confidence Score Tracking ====================

    def verify_confidence(self, ocr_results: Dict) -> Dict:
        """
        Verification Strategy 2: Confidence Score Tracking & Analysis
        Analyze per-word/character confidence scores.
        """
        engine_results = ocr_results.get('engine_results', {})
        consensus = ocr_results.get('consensus', {})

        # Collect all confidence scores
        confidences = []

        for engine, result in engine_results.items():
            conf = result.get('confidence', 0.0)
            if conf > 0:
                confidences.append(conf)

        if not confidences:
            return {
                'average_confidence': 0.0,
                'status': 'no_confidence_data'
            }

        avg_confidence = np.mean(confidences)
        min_confidence = np.min(confidences)
        max_confidence = np.max(confidences)

        # Categorize by threshold
        thresholds = CONFIDENCE_VERIFICATION_CONFIG['thresholds']

        if avg_confidence >= thresholds['excellent']:
            category = 'excellent'
        elif avg_confidence >= thresholds['good']:
            category = 'good'
        elif avg_confidence >= thresholds['uncertain']:
            category = 'uncertain'
        else:
            category = 'poor'

        # Find low-confidence words/regions
        low_confidence_regions = []

        for engine, result in engine_results.items():
            if 'word_boxes' in result and result['word_boxes']:
                for word_box in result['word_boxes']:
                    if word_box.get('confidence', 1.0) < CONFIDENCE_VERIFICATION_CONFIG['flag_below_threshold']:
                        low_confidence_regions.append({
                            'engine': engine,
                            'text': word_box.get('text', ''),
                            'confidence': word_box.get('confidence', 0.0),
                            'bbox': word_box.get('bbox')
                        })

        return {
            'average_confidence': avg_confidence,
            'min_confidence': min_confidence,
            'max_confidence': max_confidence,
            'category': category,
            'low_confidence_regions': low_confidence_regions[:50],  # Limit to top 50
            'low_confidence_count': len(low_confidence_regions),
            'status': 'pass' if category in ['excellent', 'good'] else 'review_needed'
        }

    # ==================== V3: Language Model Validation ====================

    def verify_language_model(self, text: str) -> Dict:
        """
        Verification Strategy 3: Language Model Validation & Perplexity Analysis
        Detect nonsensical or improbable text.
        """
        report = {
            'perplexity_analysis': {},
            'ner_results': {},
            'grammar_check': {},
            'anomalies': []
        }

        # Calculate perplexity for sentences
        sentences = self._split_sentences(text)

        if self.language_model:
            perplexities = []
            high_perplexity_sentences = []

            for sent in sentences[:100]:  # Limit to first 100 sentences
                perplexity = self._calculate_perplexity(sent)
                perplexities.append(perplexity)

                if perplexity > LANGUAGE_MODEL_VERIFICATION_CONFIG['perplexity_threshold']:
                    high_perplexity_sentences.append({
                        'sentence': sent[:100],  # First 100 chars
                        'perplexity': perplexity
                    })

            report['perplexity_analysis'] = {
                'average_perplexity': np.mean(perplexities) if perplexities else 0.0,
                'max_perplexity': np.max(perplexities) if perplexities else 0.0,
                'high_perplexity_sentences': high_perplexity_sentences[:10]  # Top 10
            }

        # Named Entity Recognition
        if self.ner_pipeline:
            entities = self.ner_pipeline(text[:1000])  # First 1000 chars
            report['ner_results'] = {
                'entities': entities,
                'entity_count': len(entities)
            }

        # Grammar checking (simplified)
        report['grammar_check'] = self._basic_grammar_check(text)

        return report

    def _calculate_perplexity(self, text: str) -> float:
        """Calculate perplexity score for text."""
        if not self.language_model:
            return 0.0

        try:
            import torch

            # Tokenize
            inputs = self.lm_tokenizer(text, return_tensors='pt', truncation=True, max_length=512)

            with torch.no_grad():
                outputs = self.lm_model(**inputs, labels=inputs['input_ids'])
                loss = outputs.loss

            perplexity = torch.exp(loss).item()

            return perplexity

        except Exception as e:
            self.logger.debug(f"Perplexity calculation failed: {e}")
            return 0.0

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re

        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _basic_grammar_check(self, text: str) -> Dict:
        """Basic grammar checks."""
        # Simplified checks
        issues = []

        # Check for repeated words
        words = text.lower().split()
        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                issues.append({
                    'type': 'repeated_word',
                    'word': words[i]
                })

        # Check for unusual patterns
        if re.search(r'\d{5,}', text):  # Very long numbers
            issues.append({'type': 'unusual_number_sequence'})

        if re.search(r'[A-Z]{10,}', text):  # Very long uppercase sequences
            issues.append({'type': 'unusual_uppercase_sequence'})

        return {
            'issues': issues[:20],  # Limit to 20
            'issue_count': len(issues)
        }

    # ==================== V4: Historical & Contextual Validation ====================

    def verify_historical_context(self, text: str) -> Dict:
        """
        Verification Strategy 4: Historical & Contextual Validation
        Verify content against known historical facts.
        """
        anomalies = []

        # Check for known correspondents
        mentioned_people = []
        for person in KNOWN_CORRESPONDENTS:
            if person.lower() in text.lower():
                mentioned_people.append(person)

        # Check for historical events
        mentioned_events = []
        for year, event in HISTORICAL_EVENTS.items():
            if str(year) in text or event.lower() in text.lower():
                mentioned_events.append({'year': year, 'event': event})

        # Check for dates
        import re
        dates = re.findall(r'\b(1[89]\d{2}|19[0-4]\d)\b', text)

        date_range = HISTORICAL_VERIFICATION_CONFIG['date_range']
        out_of_range_dates = [int(d) for d in dates if int(d) < date_range[0] or int(d) > date_range[1]]

        if out_of_range_dates:
            anomalies.append({
                'type': 'date_out_of_range',
                'dates': out_of_range_dates
            })

        # Check for anachronisms (post-1926 references if publication year is 1926)
        pub_year = DOCUMENT_METADATA['original_publication_year']
        future_dates = [int(d) for d in dates if int(d) > pub_year]

        if future_dates:
            anomalies.append({
                'type': 'anachronism',
                'future_dates': future_dates
            })

        return {
            'mentioned_people': mentioned_people,
            'mentioned_events': mentioned_events,
            'date_analysis': {
                'dates_found': [int(d) for d in dates],
                'out_of_range': out_of_range_dates,
                'anachronisms': future_dates
            },
            'anomalies': anomalies,
            'status': 'pass' if not anomalies else 'review_recommended'
        }

    # ==================== V5: Manual Sampling & QA ====================

    def generate_sampling_plan(self, ocr_results: Dict, total_pages: int = 211) -> Dict:
        """
        Verification Strategy 5: Manual Sampling & Statistical Quality Control
        Generate plan for human review.
        """
        config = MANUAL_VERIFICATION_CONFIG

        # Calculate sample size
        sample_percentage = config['random_sample_percentage']
        random_sample_size = int(total_pages * sample_percentage)

        # Always review specific pages
        always_review = config['always_review_pages']

        # Generate random sample (excluding always-review pages)
        all_pages = set(range(1, total_pages + 1))
        always_review_set = set([p if p > 0 else total_pages + 1 + p for p in always_review])

        available_for_random = all_pages - always_review_set
        random_sample = random.sample(list(available_for_random), min(random_sample_size, len(available_for_random)))

        # Pages requiring review due to flags
        flagged_pages = []  # Would be populated from actual analysis

        return {
            'total_pages': total_pages,
            'always_review_pages': list(always_review_set),
            'random_sample_pages': sorted(random_sample),
            'flagged_pages': flagged_pages,
            'total_manual_review_pages': len(always_review_set) + len(random_sample) + len(flagged_pages),
            'sample_percentage': (len(always_review_set) + len(random_sample)) / total_pages * 100,
            'target_cer': config['target_cer'],
            'target_wer': config['target_wer']
        }

    # ==================== V6: Diff Visualization ====================

    def generate_diff_visualization(self, ocr_results: Dict) -> Dict:
        """
        Verification Strategy 6: Diff Visualization & Interactive Review Interface
        Generate data for visual comparison.
        """
        engine_results = ocr_results.get('engine_results', {})
        consensus = ocr_results.get('consensus', {})

        if not engine_results:
            return {'status': 'no_data'}

        # Generate character-level diff for each engine vs consensus
        consensus_text = consensus.get('text', '')

        diffs = {}

        for engine, result in engine_results.items():
            engine_text = result.get('text', '')

            if engine_text:
                diff = self._generate_diff(consensus_text, engine_text)
                diffs[engine] = diff

        return {
            'consensus_text': consensus_text[:5000],  # First 5000 chars
            'engine_diffs': diffs,
            'visualization_data': {
                'needs_review': bool(diffs),
                'disagreement_count': sum(d['difference_count'] for d in diffs.values())
            }
        }

    def _generate_diff(self, text1: str, text2: str) -> Dict:
        """Generate diff between two texts."""
        matcher = SequenceMatcher(None, text1, text2)

        differences = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                differences.append({
                    'type': tag,
                    'text1_span': (i1, i2),
                    'text2_span': (j1, j2),
                    'text1_content': text1[i1:i2][:100],
                    'text2_content': text2[j1:j2][:100]
                })

        return {
            'similarity': matcher.ratio(),
            'difference_count': len(differences),
            'differences': differences[:50]  # Limit to 50
        }

    # ==================== Overall Quality & Recommendations ====================

    def _calculate_overall_quality(self, report: Dict) -> Dict:
        """Calculate overall quality score from all verifications."""
        scores = []

        # Consensus score
        if 'consensus' in report['verifications']:
            scores.append(report['verifications']['consensus'].get('agreement_score', 0.0))

        # Confidence score
        if 'confidence' in report['verifications']:
            scores.append(report['verifications']['confidence'].get('average_confidence', 0.0))

        # Overall score
        overall_score = np.mean(scores) if scores else 0.0

        # Classification
        if overall_score >= 0.95:
            quality = 'excellent'
        elif overall_score >= 0.85:
            quality = 'good'
        elif overall_score >= 0.70:
            quality = 'acceptable'
        else:
            quality = 'needs_improvement'

        return {
            'overall_score': overall_score,
            'quality': quality,
            'scores': scores,
            'flag_count': len(report.get('flags', []))
        }

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate actionable recommendations based on verification results."""
        recommendations = []

        # Based on flags
        for flag in report.get('flags', []):
            if flag['type'] == 'low_consensus':
                recommendations.append("Manual review recommended due to low OCR engine consensus")

            elif flag['type'] == 'low_confidence':
                recommendations.append("Re-scan pages with enhanced preprocessing settings")

            elif flag['type'] == 'high_perplexity':
                recommendations.append("Review flagged sentences for OCR errors")

            elif flag['type'] == 'historical_anomaly':
                recommendations.append("Verify dates and historical references")

        # Based on overall quality
        quality = report['overall_quality'].get('quality', '')

        if quality == 'needs_improvement':
            recommendations.append("Consider re-processing with adjusted OCR parameters")
            recommendations.append("Increase manual review sampling percentage")

        if not recommendations:
            recommendations.append("Quality is acceptable - proceed with minimal manual review")

        return list(set(recommendations))  # Remove duplicates


if __name__ == '__main__':
    # Test verification suite
    logging.basicConfig(level=logging.DEBUG)

    suite = VerificationSuite()

    # Example usage would require actual OCR results
    print("Verification suite initialized with 6 strategies")
