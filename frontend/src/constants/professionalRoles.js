export const PROFESSIONAL_ROLES = [
  'CEO',
  'CFO',
  'COO',
  'Division Head',
  'Manager',
  'Project Manager',
  'Team Member',
  'Individual Contributor',
  'Other',
]

export const OTHER_ROLE = 'Other'
export const DEFAULT_ROLE = 'Team Member'

export function displayProfessionalRole(role, roleOther) {
  if (role === OTHER_ROLE && roleOther) return roleOther
  return role || DEFAULT_ROLE
}

/** Map stored job_title back to dropdown + optional Other text. */
export function parseStoredRole(jobTitle) {
  if (!jobTitle) return { selectedRole: DEFAULT_ROLE, roleOther: '' }
  if (PROFESSIONAL_ROLES.includes(jobTitle)) {
    return { selectedRole: jobTitle, roleOther: '' }
  }
  return { selectedRole: OTHER_ROLE, roleOther: jobTitle }
}

export function resolveRoleForSave(selectedRole, roleOther) {
  if (selectedRole === OTHER_ROLE) {
    const custom = (roleOther || '').trim()
    return custom || null
  }
  return selectedRole || null
}

export function contactRoleFromApi(contact) {
  const role = contact?.role || DEFAULT_ROLE
  const roleOther = contact?.role_other || ''
  if (PROFESSIONAL_ROLES.includes(role)) {
    return { selectedRole: role, roleOther: role === OTHER_ROLE ? roleOther : '' }
  }
  return parseStoredRole(role)
}
