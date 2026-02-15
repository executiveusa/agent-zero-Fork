"""
Email Sequence Skill for Agent Zero
Creates email nurturing sequences for marketing campaigns
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class EmailType(Enum):
    WELCOME = "welcome"
    VALUE = "value"
    CASE_STUDY = "case_study"
    OBJECTION = "objection"
    URGENCY = "urgency"
    CLOSE = "close"


@dataclass
class Email:
    """A single email in a sequence"""
    email_id: str
    email_type: EmailType
    subject: str
    preview: str
    body: str
    send_delay_days: int
    cta: str


class EmailSequenceSkill:
    """
    Skill for creating email nurturing sequences.
    
    Capabilities:
    - Create welcome sequences
    - Generate value-add emails
    - Handle objections via email
    - Create urgency and close sequences
    """
    
    name = "email_sequence"
    description = "Create email nurturing sequences for leads"
    
    def __init__(self):
        self.sequence_types = [
            "cold_traffic",
            "warm_lead",
            "abandoned_cart",
            "post_purchase",
            "re_engagement"
        ]
    
    def create_cold_traffic_sequence(self, avatar: Dict[str, Any], offer: str) -> List[Email]:
        """Create email sequence for cold traffic"""
        emails = []
        
        # Email 1: Welcome + Lead Magnet Delivery
        emails.append(Email(
            email_id="email_1",
            email_type=EmailType.WELCOME,
            subject=f"Here's your {avatar.get('lead_magnet', 'Free Guide')}",
            preview="Your download is ready...",
            body=f"""
Hey there,

Thanks for grabbing the {avatar.get('lead_magnet', 'Free Guide')}!

Here's your download link: [DOWNLOAD LINK]

Over the next few days, I'll share some specific strategies 
that have helped {avatar.get('identity', 'people like you')} 
achieve {avatar.get('goal', 'their goals')}.

Talk soon,
[Your Name]

P.S. Quick question: What's your biggest challenge with 
{avatar.get('topic', 'this topic')} right now? Just hit reply 
and let me know - I read every email.
""",
            send_delay_days=0,
            cta="Download Now"
        ))
        
        # Email 2: Value Add
        emails.append(Email(
            email_id="email_2",
            email_type=EmailType.VALUE,
            subject=f"The {avatar.get('identity', 'Professional')}\'s Secret to {avatar.get('goal', 'Success')}",
            preview="This one change changed everything...",
            body=f"""
Hey,

Yesterday I mentioned I'd share some strategies that work.

Here's the thing most {avatar.get('identity', 'people')} get wrong:

They focus on [COMMON_MISTAKE] instead of [REAL_SOLUTION].

When I made this shift, everything changed:
- [Result 1]
- [Result 2]
- [Result 3]

Tomorrow I'll show you exactly how to implement this.

[Your Name]
""",
            send_delay_days=1,
            cta="Learn More"
        ))
        
        # Email 3: Case Study
        emails.append(Email(
            email_id="email_3",
            email_type=EmailType.CASE_STUDY,
            subject=f"How {avatar.get('case_study_name', 'Sarah')} went from {avatar.get('before_state', 'struggling')} to {avatar.get('after_state', 'thriving')}",
            preview="A real story from someone like you...",
            body=f"""
Hey,

Remember the strategy I shared yesterday?

Here's how it played out for {avatar.get('case_study_name', 'Sarah')}:

**Before:**
- {avatar.get('before_state', 'Struggling with manual processes')}
- {avatar.get('pain_point', 'Wasting hours every week')}
- {avatar.get('frustration', 'Frustrated with results')}

**After:**
- {avatar.get('after_state', 'Automated everything')}
- {avatar.get('gain', 'Saving 10+ hours per week')}
- {avatar.get('success', 'Seeing real results')}

The difference? She used {offer}.

Want similar results? Here's how to get started:
[CTA LINK]

[Your Name]
""",
            send_delay_days=2,
            cta="Get Started"
        ))
        
        # Email 4: Objection Handling
        emails.append(Email(
            email_id="email_4",
            email_type=EmailType.OBJECTION,
            subject="But what if it doesn't work for me?",
            preview="I understand the hesitation...",
            body=f"""
Hey,

I get it. You might be thinking:

"This sounds great, but will it work for ME?"

Here's the truth - {offer} works for anyone who:
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

And if you're worried about [COMMON_FEAR], don't be.
We have [GUARANTEE/SUPPORT].

Plus, here's what others are saying:
"[TESTIMONIAL 1]"
"[TESTIMONIAL 2]"

Ready to give it a shot?
[CTA LINK]

[Your Name]
""",
            send_delay_days=3,
            cta="Try It Risk-Free"
        ))
        
        # Email 5: Urgency/Close
        emails.append(Email(
            email_id="email_5",
            email_type=EmailType.URGENCY,
            subject=f"Last chance: {offer} doors closing soon",
            preview="Don't miss this...",
            body=f"""
Hey,

This is it.

In [X] hours, {offer} will be closing.

If you've been on the fence, now's the time.

Remember:
- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

And with [GUARANTEE], there's no risk.

Click here to join before it's too late:
[CTA LINK]

See you inside,
[Your Name]

P.S. Don't let another opportunity pass by. 
This is your moment.
""",
            send_delay_days=4,
            cta="Join Now"
        ))
        
        return emails
    
    def generate_sequence_report(self, emails: List[Email]) -> str:
        """Generate a markdown report of the email sequence"""
        report = "# Email Sequence\n\n"
        report += f"**Total Emails:** {len(emails)}\n\n"
        
        for email in emails:
            report += f"## Email {email.email_id}: {email.subject}\n\n"
            report += f"- **Type:** {email.email_type.value}\n"
            report += f"- **Preview:** {email.preview}\n"
            report += f"- **Send Delay:** Day {email.send_delay_days}\n"
            report += f"- **CTA:** {email.cta}\n\n"
            report += f"```\n{email.body}\n```\n\n"
            report += "---\n\n"
        
        return report


# Skill registration
skill = EmailSequenceSkill()