-- Migration 004: Add position email templates

-- Template A1: Request clarification for incomplete position details
INSERT INTO email_templates (id, name, type, subject_template, body_template, category, created_at)
VALUES (
    'A1',
    'Position Clarification Request',
    'position_clarification',
    'Need more details: {position_title}',
    'Hi {hiring_manager_name},

Thank you for submitting the position request for {position_title}.

To help us post this position effectively, we need a few more details:

{missing_info}

Could you please provide this information so we can proceed with posting the position?

Best regards,
Hellio HR Team',
    'position',
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    body_template = EXCLUDED.body_template;

-- Template A3: Position created confirmation with candidate matches
INSERT INTO email_templates (id, name, type, subject_template, body_template, category, created_at)
VALUES (
    'A3',
    'Position Created - Candidates Found',
    'position_confirmation',
    'Position posted: {position_title} - {candidate_count} matching candidates',
    'Hi {hiring_manager_name},

Great news! Your position for {position_title} has been posted successfully.

We found {candidate_count} candidates in our database who match this role:

{candidate_list}

Next steps:
- Review the candidate profiles
- Let us know who you''d like to interview
- We''ll coordinate the interview process

Position details have been added to the system and are visible to the team.

Best regards,
Hellio HR Team',
    'position',
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    body_template = EXCLUDED.body_template;

-- Template A4: Position created but no matches
INSERT INTO email_templates (id, name, type, subject_template, body_template, category, created_at)
VALUES (
    'A4',
    'Position Created - No Matches Yet',
    'position_confirmation',
    'Position posted: {position_title}',
    'Hi {hiring_manager_name},

Your position for {position_title} has been posted successfully!

We haven''t found matching candidates in our current database yet, but we''ll notify you as soon as qualified candidates apply.

The position is now active and candidates can start applying.

Best regards,
Hellio HR Team',
    'position',
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    body_template = EXCLUDED.body_template;
