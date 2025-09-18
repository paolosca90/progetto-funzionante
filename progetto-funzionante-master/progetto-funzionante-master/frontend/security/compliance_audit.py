"""
Compliance and Audit Module

Provides comprehensive compliance and audit capabilities including:
- Regulatory compliance frameworks (GDPR, HIPAA, PCI DSS, SOC 2)
- Audit trail management
- Compliance reporting
- Risk assessment
- Policy management
- User access auditing
- Data privacy enforcement
- Security control validation
- Third-party compliance
- Continuous compliance monitoring

"""

import json
import time
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class ComplianceFramework(Enum):
    """Compliance frameworks"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC_2 = "soc_2"
    ISO_27001 = "iso_27001"
    NIST_CSF = "nist_csf"
    CIS_CONTROLS = "cis_controls"
    CCPA = "ccpa"

class ComplianceStatus(Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_ASSESSED = "not_assessed"
    IN_PROGRESS = "in_progress"

class RiskLevel(Enum):
    """Risk levels"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    MINIMAL = 4

class AuditType(Enum):
    """Audit types"""
    INTERNAL = "internal"
    EXTERNAL = "external"
    REGULATORY = "regulatory"
    THIRD_PARTY = "third_party"
    AUTOMATED = "automated"
    MANUAL = "manual"

@dataclass
class ComplianceRequirement:
    """Compliance requirement"""
    requirement_id: str
    framework: ComplianceFramework
    category: str
    title: str
    description: str
    control_objective: str
    implementation_status: ComplianceStatus
    evidence_required: List[str]
    testing_procedures: List[str]
    risk_level: RiskLevel
    last_assessed: Optional[datetime] = None
    next_assessment_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    compliance_score: float = 0.0

@dataclass
class AuditRecord:
    """Audit record"""
    audit_id: str
    audit_type: AuditType
    timestamp: datetime
    user_id: Optional[str]
    action: str
    resource: Optional[str]
    result: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    session_id: Optional[str]
    risk_score: float = 0.0
    compliance_impact: bool = False
    evidence_references: List[str] = field(default_factory=list)
    reviewer_notes: List[str] = field(default_factory=list)

@dataclass
class ComplianceAssessment:
    """Compliance assessment result"""
    assessment_id: str
    framework: ComplianceFramework
    assessment_date: datetime
    assessor: str
    overall_score: float
    requirements_assessed: int
    compliant_requirements: int
    non_compliant_requirements: int
    partial_compliance: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    recommendations: List[str]
    evidence_artifacts: List[str]
    next_review_date: datetime
    status: ComplianceStatus

class DataPrivacyManager:
    """Data privacy and GDPR compliance management"""

    def __init__(self):
        self.data_subject_requests = []
        self.consent_records = {}
        self.data_processing_activities = {}
        self.data_retention_policies = {}
        self.privacy_impact_assessments = []

    def log_data_processing_activity(self, activity_type: str, data_subject: str,
                                   data_categories: List[str], purpose: str,
                                   legal_basis: str, retention_period: str):
        """Log data processing activity"""
        activity_id = f"dpa_{uuid.uuid4().hex[:8]}"
        activity = {
            'activity_id': activity_id,
            'activity_type': activity_type,
            'data_subject': data_subject,
            'data_categories': data_categories,
            'purpose': purpose,
            'legal_basis': legal_basis,
            'retention_period': retention_period,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.data_processing_activities[activity_id] = activity
        return activity_id

    def record_consent(self, user_id: str, consent_type: str, consent_given: bool,
                      document_version: str, ip_address: str):
        """Record user consent"""
        consent_id = f"consent_{uuid.uuid4().hex[:8]}"
        consent_record = {
            'consent_id': consent_id,
            'user_id': user_id,
            'consent_type': consent_type,
            'consent_given': consent_given,
            'document_version': document_version,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': ip_address,
            'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat()
        }
        self.consent_records[consent_id] = consent_record
        return consent_id

    def handle_data_subject_request(self, request_type: str, user_id: str,
                                  request_details: Dict[str, Any]) -> str:
        """Handle data subject requests (access, rectification, deletion)"""
        request_id = f"dsr_{uuid.uuid4().hex[:8]}"
        request = {
            'request_id': request_id,
            'request_type': request_type,
            'user_id': user_id,
            'request_details': request_details,
            'status': 'received',
            'timestamp': datetime.utcnow().isoformat(),
            'due_date': (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        self.data_subject_requests.append(request)
        return request_id

    def conduct_privacy_impact_assessment(self, system_name: str, data_processing: str,
                                       risks: List[str], mitigation_measures: List[str]) -> str:
        """Conduct Privacy Impact Assessment"""
        pia_id = f"pia_{uuid.uuid4().hex[:8]}"
        pia = {
            'pia_id': pia_id,
            'system_name': system_name,
            'data_processing': data_processing,
            'risks_identified': risks,
            'mitigation_measures': mitigation_measures,
            'assessment_date': datetime.utcnow().isoformat(),
            'assessor': 'compliance_team',
            'approval_status': 'pending'
        }
        self.privacy_impact_assessments.append(pia)
        return pia_id

class ComplianceEngine:
    """Compliance assessment engine"""

    def __init__(self):
        self.compliance_requirements = self._load_compliance_requirements()
        self.assessment_history = []
        self.compliance_scores = {}
        self.control_mappings = self._load_control_mappings()

    def _load_compliance_requirements(self) -> Dict[str, ComplianceRequirement]:
        """Load compliance requirements for different frameworks"""
        requirements = {}

        # GDPR Requirements
        gdpr_requirements = [
            ComplianceRequirement(
                requirement_id="GDPR_001",
                framework=ComplianceFramework.GDPR,
                category="Data Protection Principles",
                title="Lawfulness, fairness and transparency",
                description="Personal data shall be processed lawfully, fairly and in a transparent manner",
                control_objective="Ensure all data processing has lawful basis and is transparent to data subjects",
                implementation_status=ComplianceStatus.NOT_ASSESSED,
                evidence_required=["Privacy Policy", "Consent Records", "Data Processing Inventory"],
                testing_procedures=["Review privacy policy", "Audit consent records", "Verify data processing documentation"],
                risk_level=RiskLevel.HIGH
            ),
            ComplianceRequirement(
                requirement_id="GDPR_002",
                framework=ComplianceFramework.GDPR,
                category="Data Subject Rights",
                title="Right to access",
                description="Data subjects have the right to access their personal data",
                control_objective="Enable data subjects to access their personal data upon request",
                implementation_status=ComplianceStatus.NOT_ASSESSED,
                evidence_required=["Data Subject Request Procedures", "Access Logs", "Response Templates"],
                testing_procedures=["Test data access request process", "Review response times", "Verify data accuracy"],
                risk_level=RiskLevel.MEDIUM
            ),
            ComplianceRequirement(
                requirement_id="GDPR_003",
                framework=ComplianceFramework.GDPR,
                category="Data Security",
                title="Appropriate technical measures",
                description="Implement appropriate technical measures to ensure data security",
                control_objective="Protect personal data from unauthorized access, alteration, or destruction",
                implementation_status=ComplianceStatus.NOT_ASSESSED,
                evidence_required=["Security Policies", "Encryption Documentation", "Access Control Lists"],
                testing_procedures=["Review security controls", "Test encryption implementation", "Audit access controls"],
                risk_level=RiskLevel.CRITICAL
            )
        ]

        # PCI DSS Requirements
        pci_requirements = [
            ComplianceRequirement(
                requirement_id="PCI_001",
                framework=ComplianceFramework.PCI_DSS,
                category="Build and Maintain a Secure Network",
                title="Install and maintain a firewall configuration",
                description="Install and maintain a firewall configuration to protect cardholder data",
                control_objective="Protect cardholder data from unauthorized network access",
                implementation_status=ComplianceStatus.NOT_ASSESSED,
                evidence_required=["Firewall Configuration", "Network Diagrams", "Change Records"],
                testing_procedures=["Review firewall rules", "Verify network segmentation", "Test configuration"],
                risk_level=RiskLevel.CRITICAL
            ),
            ComplianceRequirement(
                requirement_id="PCI_002",
                framework=ComplianceFramework.PCI_DSS,
                category="Protect Cardholder Data",
                title="Protect stored cardholder data",
                description="Protect stored cardholder data through encryption and access controls",
                control_objective="Ensure cardholder data is encrypted and access is restricted",
                implementation_status=ComplianceStatus.NOT_ASSESSED,
                evidence_required=["Encryption Configuration", "Access Logs", "Key Management Procedures"],
                testing_procedures=["Verify encryption implementation", "Test access controls", "Review key management"],
                risk_level=RiskLevel.CRITICAL
            )
        ]

        # SOC 2 Requirements
        soc2_requirements = [
            ComplianceRequirement(
                requirement_id="SOC2_001",
                framework=ComplianceFramework.SOC_2,
                category="Security",
                title="Access Control Management",
                description="Implement logical access controls to prevent unauthorized access",
                control_objective="Ensure only authorized users have access to systems and data",
                implementation_status=ComplianceStatus.NOT_ASSESSED,
                evidence_required=["Access Control Policy", "User Access Reviews", "Termination Procedures"],
                testing_procedures=["Review user access", "Test authentication controls", "Audit access logs"],
                risk_level=RiskLevel.HIGH
            ),
            ComplianceRequirement(
                requirement_id="SOC2_002",
                framework=ComplianceFramework.SOC_2,
                category="Availability",
                title="System Monitoring",
                description="Monitor systems to ensure availability and performance",
                control_objective="Maintain system availability and performance metrics",
                implementation_status=ComplianceStatus.NOT_ASSESSED,
                evidence_required=["Monitoring Procedures", "Performance Metrics", "Incident Response Plan"],
                testing_procedures=["Review monitoring logs", "Test alerting systems", "Verify backup procedures"],
                risk_level=RiskLevel.MEDIUM
            )
        ]

        # Add all requirements
        for req in gdpr_requirements + pci_requirements + soc2_requirements:
            requirements[req.requirement_id] = req

        return requirements

    def _load_control_mappings(self) -> Dict[str, List[str]]:
        """Load control mappings between frameworks"""
        return {
            "GDPR_001": ["PCI_001", "SOC2_001"],  # Maps to PCI and SOC2 security controls
            "GDPR_003": ["PCI_002", "SOC2_001"],  # Maps to PCI encryption and SOC2 access controls
            "SOC2_001": ["GDPR_003", "PCI_002"],  # Cross-mapping
        }

    def assess_compliance(self, framework: ComplianceFramework) -> ComplianceAssessment:
        """Assess compliance for a specific framework"""
        framework_requirements = [
            req for req in self.compliance_requirements.values()
            if req.framework == framework
        ]

        if not framework_requirements:
            raise ValueError(f"No requirements found for framework: {framework}")

        # Assess each requirement
        compliant_count = 0
        non_compliant_count = 0
        partial_count = 0
        critical_findings = 0
        high_findings = 0
        medium_findings = 0
        low_findings = 0
        recommendations = []
        artifacts = []

        for requirement in framework_requirements:
            assessment_result = self._assess_requirement(requirement)
            requirement.implementation_status = assessment_result['status']
            requirement.compliance_score = assessment_result['score']
            requirement.last_assessed = datetime.utcnow()

            # Count findings
            if assessment_result['status'] == ComplianceStatus.COMPLIANT:
                compliant_count += 1
            elif assessment_result['status'] == ComplianceStatus.NON_COMPLIANT:
                non_compliant_count += 1
                if requirement.risk_level == RiskLevel.CRITICAL:
                    critical_findings += 1
                elif requirement.risk_level == RiskLevel.HIGH:
                    high_findings += 1
                elif requirement.risk_level == RiskLevel.MEDIUM:
                    medium_findings += 1
                else:
                    low_findings += 1
            elif assessment_result['status'] == ComplianceStatus.PARTIALLY_COMPLIANT:
                partial_count += 1
                if requirement.risk_level == RiskLevel.HIGH:
                    high_findings += 1
                elif requirement.risk_level == RiskLevel.MEDIUM:
                    medium_findings += 1
                else:
                    low_findings += 1

            # Collect recommendations
            recommendations.extend(assessment_result['recommendations'])
            artifacts.extend(assessment_result['artifacts'])

        # Calculate overall score
        total_requirements = len(framework_requirements)
        overall_score = (compliant_count + partial_count * 0.5) / total_requirements * 100 if total_requirements > 0 else 0

        # Determine overall status
        if overall_score >= 90:
            status = ComplianceStatus.COMPLIANT
        elif overall_score >= 70:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT

        assessment = ComplianceAssessment(
            assessment_id=f"assessment_{uuid.uuid4().hex[:8]}",
            framework=framework,
            assessment_date=datetime.utcnow(),
            assessor="compliance_engine",
            overall_score=overall_score,
            requirements_assessed=total_requirements,
            compliant_requirements=compliant_count,
            non_compliant_requirements=non_compliant_count,
            partial_compliance=partial_count,
            critical_findings=critical_findings,
            high_findings=high_findings,
            medium_findings=medium_findings,
            low_findings=low_findings,
            recommendations=list(set(recommendations)),
            evidence_artifacts=list(set(artifacts)),
            next_review_date=datetime.utcnow() + timedelta(days=90),
            status=status
        )

        self.assessment_history.append(assessment)
        return assessment

    def _assess_requirement(self, requirement: ComplianceRequirement) -> Dict[str, Any]:
        """Assess individual requirement"""
        # This would be implemented with actual assessment logic
        # For now, we'll simulate assessment based on requirement metadata

        # Simulate assessment logic
        assessment_result = {
            'status': ComplianceStatus.COMPLIANT,  # Default to compliant for demo
            'score': 100.0,
            'recommendations': [],
            'artifacts': [],
            'evidence': []
        }

        # In a real implementation, this would:
        # 1. Check if controls are implemented
        # 2. Review evidence and documentation
        # 3. Test control effectiveness
        # 4. Interview personnel
        # 5. Review logs and monitoring data

        return assessment_result

    def generate_compliance_report(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        assessment = self.assess_compliance(framework)

        framework_requirements = [
            req for req in self.compliance_requirements.values()
            if req.framework == framework
        ]

        report = {
            'report_id': f"report_{uuid.uuid4().hex[:8]}",
            'framework': framework.value,
            'report_date': datetime.utcnow().isoformat(),
            'executive_summary': {
                'overall_score': assessment.overall_score,
                'compliance_status': assessment.status.value,
                'total_requirements': assessment.requirements_assessed,
                'critical_findings': assessment.critical_findings,
                'high_risk_findings': assessment.high_findings,
                'recommendations_count': len(assessment.recommendations)
            },
            'detailed_findings': {
                'requirement_breakdown': [
                    {
                        'requirement_id': req.requirement_id,
                        'title': req.title,
                        'category': req.category,
                        'status': req.implementation_status.value,
                        'risk_level': req.risk_level.name,
                        'compliance_score': req.compliance_score,
                        'last_assessed': req.last_assessed.isoformat() if req.last_assessed else None
                    }
                    for req in framework_requirements
                ],
                'findings_by_risk': {
                    'critical': assessment.critical_findings,
                    'high': assessment.high_findings,
                    'medium': assessment.medium_findings,
                    'low': assessment.low_findings
                }
            },
            'recommendations': assessment.recommendations,
            'evidence_artifacts': assessment.evidence_artifacts,
            'next_assessment_date': assessment.next_review_date.isoformat(),
            'assessor': assessment.assessor
        }

        return report

class AuditManager:
    """Audit trail management"""

    def __init__(self):
        self.audit_logs = []
        self.audit_policies = {}
        self.retention_policies = {}
        self.audit_alerts = []
        self.review_queue = []

    def log_audit_event(self, event_type: str, user_id: Optional[str], action: str,
                       resource: Optional[str], result: str, details: Dict[str, Any],
                       ip_address: str, user_agent: str, risk_score: float = 0.0) -> str:
        """Log audit event"""
        audit_id = f"audit_{uuid.uuid4().hex[:8]}"

        audit_record = AuditRecord(
            audit_id=audit_id,
            audit_type=AuditType.AUTOMATED,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=details.get('session_id'),
            risk_score=risk_score,
            compliance_impact=details.get('compliance_impact', False)
        )

        self.audit_logs.append(audit_record)

        # Check for alerts
        if risk_score > 7.0 or details.get('compliance_impact'):
            self._create_audit_alert(audit_record)

        return audit_id

    def _create_audit_alert(self, audit_record: AuditRecord):
        """Create audit alert"""
        alert = {
            'alert_id': f"alert_{uuid.uuid4().hex[:8]}",
            'audit_id': audit_record.audit_id,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'high' if audit_record.risk_score > 8.0 else 'medium',
            'type': 'high_risk_activity' if audit_record.risk_score > 7.0 else 'compliance_impact',
            'description': f"High-risk audit event: {audit_record.action}",
            'requires_review': True,
            'reviewed': False
        }
        self.audit_alerts.append(alert)

    def search_audit_logs(self, filters: Dict[str, Any]) -> List[AuditRecord]:
        """Search audit logs with filters"""
        filtered_logs = self.audit_logs

        # Apply filters
        if 'user_id' in filters:
            filtered_logs = [log for log in filtered_logs if log.user_id == filters['user_id']]

        if 'action' in filters:
            filtered_logs = [log for log in filtered_logs if filters['action'] in log.action]

        if 'start_date' in filters:
            start_date = filters['start_date']
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_date]

        if 'end_date' in filters:
            end_date = filters['end_date']
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_date]

        if 'min_risk_score' in filters:
            min_score = filters['min_risk_score']
            filtered_logs = [log for log in filtered_logs if log.risk_score >= min_score]

        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        return filtered_logs

    def generate_audit_report(self, start_date: datetime, end_date: datetime,
                            report_type: str = "comprehensive") -> Dict[str, Any]:
        """Generate audit report"""
        filtered_logs = [
            log for log in self.audit_logs
            if start_date <= log.timestamp <= end_date
        ]

        report = {
            'report_id': f"audit_report_{uuid.uuid4().hex[:8]}",
            'report_type': report_type,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_events': len(filtered_logs),
                'unique_users': len(set(log.user_id for log in filtered_logs if log.user_id)),
                'high_risk_events': len([log for log in filtered_logs if log.risk_score > 7.0]),
                'compliance_events': len([log for log in filtered_logs if log.compliance_impact]),
                'failed_events': len([log for log in filtered_logs if log.result == 'failed'])
            },
            'event_analysis': {
                'by_action': self._analyze_by_action(filtered_logs),
                'by_user': self._analyze_by_user(filtered_logs),
                'by_risk_level': self._analyze_by_risk(filtered_logs),
                'hourly_distribution': self._analyze_hourly_distribution(filtered_logs)
            },
            'findings': self._identify_findings(filtered_logs),
            'recommendations': self._generate_audit_recommendations(filtered_logs)
        }

        return report

    def _analyze_by_action(self, logs: List[AuditRecord]) -> Dict[str, int]:
        """Analyze events by action"""
        action_counts = {}
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
        return action_counts

    def _analyze_by_user(self, logs: List[AuditRecord]) -> Dict[str, int]:
        """Analyze events by user"""
        user_counts = {}
        for log in logs:
            if log.user_id:
                user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1
        return user_counts

    def _analyze_by_risk(self, logs: List[AuditRecord]) -> Dict[str, int]:
        """Analyze events by risk level"""
        risk_levels = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for log in logs:
            if log.risk_score >= 8.0:
                risk_levels['critical'] += 1
            elif log.risk_score >= 6.0:
                risk_levels['high'] += 1
            elif log.risk_score >= 4.0:
                risk_levels['medium'] += 1
            else:
                risk_levels['low'] += 1
        return risk_levels

    def _analyze_hourly_distribution(self, logs: List[AuditRecord]) -> Dict[str, int]:
        """Analyze hourly distribution of events"""
        hourly_counts = {}
        for log in logs:
            hour = log.timestamp.hour
            hour_key = f"{hour:02d}:00"
            hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
        return hourly_counts

    def _identify_findings(self, logs: List[AuditRecord]) -> List[Dict[str, Any]]:
        """Identify audit findings"""
        findings = []

        # Look for patterns indicating issues
        failed_logins = [log for log in logs if log.action == 'login' and log.result == 'failed']
        if len(failed_logins) > 10:
            findings.append({
                'type': 'high_failed_login_attempts',
                'description': f'Detected {len(failed_logins)} failed login attempts',
                'severity': 'high',
                'recommendation': 'Review authentication logs and consider implementing account lockout'
            })

        # Look for privilege escalation
        privilege_changes = [log for log in logs if 'privilege' in log.action.lower()]
        if len(privilege_changes) > 5:
            findings.append({
                'type': 'frequent_privilege_changes',
                'description': f'Detected {len(privilege_changes)} privilege change operations',
                'severity': 'medium',
                'recommendation': 'Review privilege change procedures and implement additional approvals'
            })

        return findings

    def _generate_audit_recommendations(self, logs: List[AuditRecord]) -> List[str]:
        """Generate audit recommendations"""
        recommendations = []

        # Check for high-risk activities
        high_risk_logs = [log for log in logs if log.risk_score > 7.0]
        if len(high_risk_logs) > len(logs) * 0.1:  # More than 10% high-risk
            recommendations.append("Implement additional controls for high-risk activities")

        # Check for failed operations
        failed_logs = [log for log in logs if log.result == 'failed']
        if len(failed_logs) > len(logs) * 0.05:  # More than 5% failures
            recommendations.append("Investigate high failure rate in system operations")

        # Check for off-hours activity
        off_hours_logs = [log for log in logs if log.timestamp.hour < 6 or log.timestamp.hour > 22]
        if len(off_hours_logs) > len(logs) * 0.2:  # More than 20% off-hours
            recommendations.append("Review off-hours activity patterns and implement additional monitoring")

        return recommendations

class ComplianceAuditSystem:
    """
    Comprehensive compliance and audit system

    Features:
    - Multi-framework compliance management
    - Automated compliance assessments
    - Comprehensive audit logging
    - Data privacy management
    - Risk assessment
    - Reporting and analytics
    """

    def __init__(self):
        self.compliance_engine = ComplianceEngine()
        self.audit_manager = AuditManager()
        self.data_privacy_manager = DataPrivacyManager()
        self.risk_assessment_engine = RiskAssessmentEngine()
        self.framework_configs = self._load_framework_configs()

    def _load_framework_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load framework-specific configurations"""
        return {
            'GDPR': {
                'data_subject_rights': True,
                'consent_management': True,
                'data_portability': True,
                'breach_notification': True,
                'retention_policies': True
            },
            'PCI_DSS': {
                'cardholder_data_protection': True,
                'network_security': True,
                'access_control': True,
                'vulnerability_management': True,
                'monitoring_and_testing': True
            },
            'SOC_2': {
                'security_controls': True,
                'availability_monitoring': True,
                'processing_integrity': True,
                'confidentiality_controls': True,
                'privacy_controls': True
            }
        }

    def perform_compliance_assessment(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """Perform comprehensive compliance assessment"""
        logger.info(f"Starting compliance assessment for {framework.value}")

        assessment = self.compliance_engine.assess_compliance(framework)
        report = self.compliance_engine.generate_compliance_report(framework)

        # Log assessment event
        self.audit_manager.log_audit_event(
            event_type='compliance_assessment',
            user_id='compliance_system',
            action=f'compliance_assessment_{framework.value}',
            resource='compliance_framework',
            result='completed',
            details={
                'framework': framework.value,
                'assessment_id': assessment.assessment_id,
                'overall_score': assessment.overall_score,
                'findings_count': assessment.critical_findings + assessment.high_findings + assessment.medium_findings + assessment.low_findings
            },
            ip_address='system',
            user_agent='compliance_system',
            risk_score=3.0
        )

        logger.info(f"Compliance assessment completed for {framework.value} - Score: {assessment.overall_score:.1f}%")
        return report

    def generate_compliance_dashboard(self) -> Dict[str, Any]:
        """Generate compliance dashboard with all frameworks"""
        dashboard = {
            'generated_at': datetime.utcnow().isoformat(),
            'frameworks': {},
            'overall_compliance_score': 0.0,
            'critical_findings': 0,
            'high_risk_items': 0,
            'upcoming_assessments': [],
            'recent_activities': []
        }

        framework_scores = []

        # Assess each framework
        for framework in ComplianceFramework:
            try:
                report = self.compliance_engine.generate_compliance_report(framework)
                dashboard['frameworks'][framework.value] = {
                    'score': report['executive_summary']['overall_score'],
                    'status': report['executive_summary']['compliance_status'],
                    'findings': report['executive_summary']['critical_findings'] + report['executive_summary']['high_risk_findings']
                }
                framework_scores.append(report['executive_summary']['overall_score'])
                dashboard['critical_findings'] += report['executive_summary']['critical_findings']
                dashboard['high_risk_items'] += report['executive_summary']['high_risk_findings']
            except Exception as e:
                logger.error(f"Error assessing framework {framework.value}: {e}")

        # Calculate overall score
        if framework_scores:
            dashboard['overall_compliance_score'] = sum(framework_scores) / len(framework_scores)

        # Get upcoming assessments
        dashboard['upcoming_assessments'] = self._get_upcoming_assessments()

        # Get recent activities
        dashboard['recent_activities'] = self._get_recent_activities()

        return dashboard

    def _get_upcoming_assessments(self) -> List[Dict[str, Any]]:
        """Get upcoming compliance assessments"""
        upcoming = []
        current_date = datetime.utcnow()

        for requirement in self.compliance_engine.compliance_requirements.values():
            if requirement.next_assessment_date and requirement.next_assessment_date > current_date:
                days_until = (requirement.next_assessment_date - current_date).days
                if days_until <= 30:  # Next 30 days
                    upcoming.append({
                        'requirement_id': requirement.requirement_id,
                        'framework': requirement.framework.value,
                        'title': requirement.title,
                        'assessment_date': requirement.next_assessment_date.isoformat(),
                        'days_until': days_until,
                        'risk_level': requirement.risk_level.name
                    })

        return sorted(upcoming, key=lambda x: x['days_until'])

    def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """Get recent compliance activities"""
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        recent_logs = [
            log for log in self.audit_manager.audit_logs
            if log.timestamp >= cutoff_date and 'compliance' in log.action.lower()
        ]

        return [
            {
                'timestamp': log.timestamp.isoformat(),
                'action': log.action,
                'user_id': log.user_id,
                'result': log.result,
                'details': log.details
            }
            for log in recent_logs[-10:]  # Last 10 activities
        ]

    def handle_data_breach(self, breach_details: Dict[str, Any]) -> str:
        """Handle data breach incident"""
        breach_id = f"breach_{uuid.uuid4().hex[:8]}"

        breach_record = {
            'breach_id': breach_id,
            'timestamp': datetime.utcnow().isoformat(),
            'breach_type': breach_details.get('type', 'unauthorized_access'),
            'data_affected': breach_details.get('data_affected', []),
            'individuals_affected': breach_details.get('individuals_affected', 0),
            'discovery_date': breach_details.get('discovery_date'),
            'containment_actions': breach_details.get('containment_actions', []),
            'notification_status': 'pending',
            'regulatory_reporting_required': breach_details.get('regulatory_reporting', False),
            'investigation_status': 'in_progress'
        }

        # Log breach event
        self.audit_manager.log_audit_event(
            event_type='data_breach',
            user_id='security_team',
            action='data_breach_detected',
            resource='data_security',
            result='breach_identified',
            details=breach_record,
            ip_address='system',
            user_agent='security_system',
            risk_score=10.0,
            compliance_impact=True
        )

        logger.critical(f"Data breach detected: {breach_id} - {breach_details.get('type', 'unknown')}")
        return breach_id

    def export_compliance_data(self, format_type: str = "json") -> str:
        """Export compliance data for external reporting"""
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'frameworks': {},
            'audit_logs': [],
            'compliance_scores': {},
            'risk_assessments': []
        }

        # Export framework data
        for framework in ComplianceFramework:
            try:
                report = self.compliance_engine.generate_compliance_report(framework)
                export_data['frameworks'][framework.value] = report
            except Exception as e:
                logger.error(f"Error exporting framework {framework.value}: {e}")

        # Export recent audit logs
        export_data['audit_logs'] = [
            {
                'audit_id': log.audit_id,
                'timestamp': log.timestamp.isoformat(),
                'user_id': log.user_id,
                'action': log.action,
                'result': log.result,
                'risk_score': log.risk_score
            }
            for log in self.audit_manager.audit_logs[-1000:]  # Last 1000 logs
        ]

        # Generate export file
        if format_type.lower() == "json":
            return json.dumps(export_data, indent=2, default=str)
        elif format_type.lower() == "csv":
            return self._export_to_csv(export_data)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _export_to_csv(self, data: Dict[str, Any]) -> str:
        """Export data to CSV format"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write audit logs to CSV
        writer.writerow(['Audit ID', 'Timestamp', 'User ID', 'Action', 'Result', 'Risk Score'])
        for log in data['audit_logs']:
            writer.writerow([
                log['audit_id'],
                log['timestamp'],
                log['user_id'],
                log['action'],
                log['result'],
                log['risk_score']
            ])

        return output.getvalue()

class RiskAssessmentEngine:
    """Risk assessment engine"""

    def __init__(self):
        self.risk_factors = {
            'data_sensitivity': {
                'public': 1,
                'internal': 3,
                'confidential': 7,
                'restricted': 10
            },
            'threat_actors': {
                'opportunistic': 2,
                'targeted': 5,
                'advanced_persistent_threat': 10
            },
            'vulnerability_severity': {
                'low': 2,
                'medium': 5,
                'high': 8,
                'critical': 10
            }
        }

    def calculate_risk_score(self, asset: str, threat: str, vulnerability: str,
                           impact_factors: Dict[str, float]) -> float:
        """Calculate risk score using standardized methodology"""
        try:
            # Get factor scores
            sensitivity_score = self.risk_factors['data_sensitivity'].get(impact_factors.get('data_sensitivity', 'internal'), 3)
            threat_score = self.risk_factors['threat_actors'].get(threat, 3)
            vulnerability_score = self.risk_factors['vulnerability_severity'].get(vulnerability, 3)

            # Calculate inherent risk
            inherent_risk = (sensitivity_score * threat_score * vulnerability_score) / 100

            # Apply control effectiveness
            control_effectiveness = impact_factors.get('control_effectiveness', 0.7)
            residual_risk = inherent_risk * (1 - control_effectiveness)

            return min(residual_risk * 10, 10.0)  # Scale to 0-10

        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 5.0

    def assess_compliance_risks(self, compliance_findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assess risks from compliance findings"""
        risk_assessments = []

        for finding in compliance_findings:
            risk_score = self.calculate_risk_score(
                asset=finding.get('asset', 'unknown'),
                threat=finding.get('threat_type', 'opportunistic'),
                vulnerability=finding.get('vulnerability_type', 'medium'),
                impact_factors={
                    'data_sensitivity': finding.get('data_sensitivity', 'internal'),
                    'control_effectiveness': finding.get('control_effectiveness', 0.5)
                }
            )

            risk_assessment = {
                'risk_id': f"risk_{uuid.uuid4().hex[:8]}",
                'finding_id': finding.get('finding_id'),
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'description': finding.get('description', ''),
                'mitigation_recommendations': self._generate_mitigation_recommendations(risk_score),
                'risk_owner': finding.get('assigned_to', 'compliance_team'),
                'review_date': (datetime.utcnow() + timedelta(days=30)).isoformat()
            }

            risk_assessments.append(risk_assessment)

        return sorted(risk_assessments, key=lambda x: x['risk_score'], reverse=True)

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 8.0:
            return 'critical'
        elif risk_score >= 6.0:
            return 'high'
        elif risk_score >= 4.0:
            return 'medium'
        elif risk_score >= 2.0:
            return 'low'
        else:
            return 'minimal'

    def _generate_mitigation_recommendations(self, risk_score: float) -> List[str]:
        """Generate mitigation recommendations based on risk score"""
        recommendations = []

        if risk_score >= 8.0:
            recommendations.extend([
                "Immediate remediation required",
                "Implement compensating controls",
                "Escalate to senior management",
                "Consider temporary suspension of affected services"
            ])
        elif risk_score >= 6.0:
            recommendations.extend([
                "Prioritize remediation within 30 days",
                "Implement additional monitoring",
                "Review control effectiveness",
                "Update risk assessment procedures"
            ])
        elif risk_score >= 4.0:
            recommendations.extend([
                "Schedule remediation within 90 days",
                "Review existing controls",
                "Consider process improvements",
                "Update documentation"
            ])
        else:
            recommendations.extend([
                "Monitor risk trend",
                "Consider during next review cycle",
                "Maintain existing controls"
            ])

        return recommendations

# Initialize global compliance system
compliance_audit_system = ComplianceAuditSystem()

# Example usage
if __name__ == "__main__":
    # Create compliance system
    system = ComplianceAuditSystem()

    # Perform compliance assessment
    gdpr_report = system.perform_compliance_assessment(ComplianceFramework.GDPR)
    print(f"GDPR Compliance Score: {gdpr_report['executive_summary']['overall_score']:.1f}%")

    # Generate dashboard
    dashboard = system.generate_compliance_dashboard()
    print(f"Overall Compliance Score: {dashboard['overall_compliance_score']:.1f}%")

    # Test data privacy features
    consent_id = system.data_privacy_manager.record_consent(
        user_id="user123",
        consent_type="data_processing",
        consent_given=True,
        document_version="1.0",
        ip_address="192.168.1.1"
    )

    dsr_id = system.data_privacy_manager.handle_data_subject_request(
        request_type="access",
        user_id="user123",
        request_details={"data_categories": ["personal_data", "usage_data"]}
    )

    print(f"Compliance and audit system initialized")
    print(f"Recorded consent: {consent_id}")
    print(f"Data subject request: {dsr_id}")