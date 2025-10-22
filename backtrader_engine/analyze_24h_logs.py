#!/usr/bin/env python3
"""
24-Hour Trading Bot Test Analyzer
Extracts and analyzes logs for comprehensive testing report
"""

import json
import re
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAnalyzer:
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.data = {
            'signals': [],
            'trades': [],
            'risk_rejections': [],
            'errors': [],
            'strategies': defaultdict(lambda: {'signals': 0, 'confidence': []}),
            'symbols': defaultdict(lambda: {'buy': 0, 'sell': 0}),
            'timeline': []
        }
        
    def load_logs(self):
        """Load and parse log files"""
        logger.info("Loading logs...")
        
        log_files = list(self.log_dir.glob("*.log"))
        for log_file in log_files:
            self._parse_log_file(log_file)
    
    def _parse_log_file(self, log_file):
        """Parse individual log file"""
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    self._parse_line(line)
        except Exception as e:
            logger.error(f"Error parsing {log_file}: {e}")
    
    def _parse_line(self, line):
        """Parse a single log line"""
        try:
            # Signal generation
            if 'BUY signal' in line or 'SELL signal' in line:
                match = re.search(r'(\w+)\s+signal.*symbol[:\s]+(\w+).*confidence[:\s]+([\d.]+)', line)
                if match:
                    signal_type, symbol, confidence = match.groups()
                    self.data['signals'].append({
                        'type': signal_type,
                        'symbol': symbol,
                        'confidence': float(confidence),
                        'timestamp': self._extract_timestamp(line)
                    })
                    self.data['symbols'][symbol][signal_type.lower()] += 1
            
            # Strategy signals
            if 'Strategy' in line and ('signal' in line or 'Signal' in line):
                match = re.search(r'(\w+Strategy).*signal', line, re.IGNORECASE)
                if match:
                    strategy = match.group(1)
                    self.data['strategies'][strategy]['signals'] += 1
            
            # Risk management rejections
            if 'Risk Manager' in line and ('reject' in line.lower() or 'reason' in line.lower()):
                self.data['risk_rejections'].append({
                    'timestamp': self._extract_timestamp(line),
                    'reason': line.strip()
                })
            
            # Errors
            if 'ERROR' in line or 'Exception' in line:
                self.data['errors'].append({
                    'timestamp': self._extract_timestamp(line),
                    'message': line.strip()
                })
            
            # Trades executed
            if 'order' in line.lower() and ('executed' in line.lower() or 'opened' in line.lower()):
                self.data['trades'].append({
                    'timestamp': self._extract_timestamp(line),
                    'details': line.strip()
                })
        
        except Exception as e:
            logger.debug(f"Error parsing line: {e}")
    
    def _extract_timestamp(self, line):
        """Extract timestamp from log line"""
        match = re.search(r'\[(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]', line)
        if match:
            return match.group(1)
        return "N/A"
    
    def generate_report(self):
        """Generate analysis report"""
        report = []
        report.append("=" * 80)
        report.append("24-HOUR TRADING BOT VALIDATION TEST - ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Test Execution Summary
        report.append("EXECUTION SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Signals Generated: {len(self.data['signals'])}")
        report.append(f"Total Trades Executed: {len(self.data['trades'])}")
        report.append(f"Risk Manager Rejections: {len(self.data['risk_rejections'])}")
        report.append(f"Errors/Exceptions: {len(self.data['errors'])}")
        report.append("")
        
        # Signal Distribution by Type
        report.append("SIGNAL DISTRIBUTION")
        report.append("-" * 80)
        buy_count = sum(1 for s in self.data['signals'] if s['type'] == 'BUY')
        sell_count = sum(1 for s in self.data['signals'] if s['type'] == 'SELL')
        report.append(f"BUY Signals: {buy_count}")
        report.append(f"SELL Signals: {sell_count}")
        report.append("")
        
        # Signals by Symbol
        report.append("SIGNALS BY SYMBOL")
        report.append("-" * 80)
        for symbol, data in sorted(self.data['symbols'].items()):
            total = data['buy'] + data['sell']
            report.append(f"{symbol}:")
            report.append(f"  - BUY:  {data['buy']}")
            report.append(f"  - SELL: {data['sell']}")
            report.append(f"  - Total: {total}")
        report.append("")
        
        # Strategy Performance
        if self.data['strategies']:
            report.append("STRATEGY PERFORMANCE")
            report.append("-" * 80)
            for strategy, stats in sorted(self.data['strategies'].items()):
                report.append(f"{strategy}:")
                report.append(f"  - Signals: {stats['signals']}")
                if stats['confidence']:
                    avg_conf = sum(stats['confidence']) / len(stats['confidence'])
                    report.append(f"  - Avg Confidence: {avg_conf:.2f}")
            report.append("")
        
        # Risk Management Analysis
        if self.data['risk_rejections']:
            report.append("RISK MANAGEMENT ANALYSIS")
            report.append("-" * 80)
            report.append(f"Total Rejections: {len(self.data['risk_rejections'])}")
            report.append("Rejection Reasons:")
            for rejection in self.data['risk_rejections'][:10]:  # Show first 10
                report.append(f"  - {rejection['reason'][:100]}")
            report.append("")
        
        # Errors
        if self.data['errors']:
            report.append("ERRORS/EXCEPTIONS")
            report.append("-" * 80)
            report.append(f"Total Errors: {len(self.data['errors'])}")
            report.append("Sample Errors (first 5):")
            for error in self.data['errors'][:5]:
                report.append(f"  - {error['message'][:100]}")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 80)
        
        if buy_count == 0 or sell_count == 0:
            report.append("- Strategies not generating balanced signals. Review signal generation logic.")
        
        if len(self.data['risk_rejections']) > len(self.data['trades']):
            report.append("- High rejection rate. Review risk limits configuration.")
        
        if len(self.data['errors']) > 10:
            report.append("- Multiple errors detected. Check error logs for patterns.")
        else:
            report.append("- System stability appears good with minimal errors.")
        
        if len(self.data['signals']) > 50:
            report.append("- Healthy signal generation observed across strategies.")
        
        report.append("")
        report.append("=" * 80)
        report.append(f"Report Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, filename="24h_test_report.txt"):
        """Save report to file"""
        report = self.generate_report()
        report_path = self.log_dir / filename
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Report saved to: {report_path}")
        return report


if __name__ == "__main__":
    analyzer = TestAnalyzer("logs")
    analyzer.load_logs()
    report = analyzer.save_report()
    print(report)
