#!/usr/bin/env python3
"""
Complete Model Analysis Runner
Runs adversarial testing, explainability analysis, and audit reporting
"""

import sys
import os
sys.path.append('src')

from src.adversarial_testing import run_adversarial_tests
from src.explainability import generate_explainability_reports
from src.audit_report import run_complete_audit

def main():
    """Run complete model analysis pipeline"""
    print("🚀 Starting Complete Model Analysis Pipeline")
    print("=" * 60)
    
    # Create output directories
    os.makedirs("outputs/adversarial_tests", exist_ok=True)
    os.makedirs("outputs/explainability", exist_ok=True)
    os.makedirs("outputs/audit_reports", exist_ok=True)
    
    try:
        # Step 1: Adversarial Testing
        print("\n📊 Step 1: Running Adversarial Testing...")
        adversarial_results = run_adversarial_tests()
        print("✅ Adversarial testing completed!")
        
        # Step 2: Explainability Analysis
        print("\n🔍 Step 2: Generating Explainability Reports...")
        explainability_results = generate_explainability_reports()
        print("✅ Explainability analysis completed!")
        
        # Step 3: Comprehensive Audit
        print("\n📋 Step 3: Generating Audit Report...")
        audit_results = run_complete_audit()
        print("✅ Audit report completed!")
        
        print("\n" + "=" * 60)
        print("🎉 ANALYSIS COMPLETE!")
        print("=" * 60)
        print("📁 Results saved in:")
        print("   • outputs/adversarial_tests/")
        print("   • outputs/explainability/")
        print("   • outputs/audit_reports/")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)