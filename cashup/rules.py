import rules

from .utils import in_editable_period


# Business rules

@rules.predicate
def is_a_business_owner(user):
    return user.profile.is_owner

@rules.predicate
def is_business_owner(user, business):
    return user.profile.business == business and user.profile.is_owner

rules.add_perm('cashup.view_business', is_business_owner)
rules.add_perm('cashup.change_business', is_business_owner)

# Personnel rules

@rules.predicate
def is_personnel_business_owner(user, personnel):
    return is_business_owner(user, personnel.business)

@rules.predicate
def is_personnel(user, personnel):
    return user.profile == personnel

rules.add_perm('cashup.view_personnel_list', is_a_business_owner)

rules.add_perm('cashup.view_personnel_tillclosure_list',
    is_personnel | is_personnel_business_owner)

rules.add_perm('cashup.view_personnel_tillclosure_audit_trail',
    is_personnel_business_owner)

# Outlet rules

@rules.predicate
def is_outlet_owner(user, outlet):
    return is_business_owner(user, outlet.business)

@rules.predicate
def is_outlet_manager(user, outlet):
    return outlet.staff.filter(personnel=user.profile, is_manager=True).exists()

@rules.predicate
def is_outlet_staff(user, outlet):
    return outlet.staff.filter(personnel=user.profile).exists()

rules.add_perm('cashup.change_outlet', is_outlet_owner | is_outlet_manager)
rules.add_perm('cashup.view_outlet', is_outlet_owner | is_outlet_staff)
rules.add_perm('cashup.create_outlet', is_a_business_owner)
rules.add_perm('cashup.view_outlet_tillclosure_audit_trail',
    is_outlet_manager | is_outlet_owner)

# TillClosure rules

@rules.predicate
def was_closed_by(user, tillcashup):
    return tillcashup.closed_by.user == user

@rules.predicate
def is_editable(user, tillcashup):
    return in_editable_period(tillcashup.close_time)

@rules.predicate
def is_not_deleted(user, tillcashup):
    return not tillcashup.is_deleted

@rules.predicate
def is_tillclosure_outlet_owner(user, tillcashup):
    return is_outlet_owner(user, tillcashup.outlet)

@rules.predicate
def is_tillclosure_outlet_manager(user, tillcashup):
    return is_outlet_manager(user, tillcashup.outlet)

@rules.predicate
def is_tillclosure_outlet_staff(user, tillcashup):
    return is_outlet_staff(user, tillcashup.outlet)

is_staff_and_is_editable = is_tillclosure_outlet_staff & is_editable & \
    is_not_deleted
is_staff_and_is_not_deleted = is_tillclosure_outlet_staff & is_not_deleted

rules.add_perm('cashup.view_tillclosures_for_outlet',
    is_outlet_staff | is_outlet_owner)

rules.add_perm('cashup.create_tillclosure_for_outlet',
    is_outlet_staff | is_outlet_owner)

rules.add_perm('cashup.view_tillclosure',
    is_staff_and_is_not_deleted | is_tillclosure_outlet_manager | \
        is_tillclosure_outlet_owner)

# TODO: do I need this??
rules.add_rule('cashup.change_tillclosure',
    is_staff_and_is_editable | is_tillclosure_outlet_owner)

rules.add_perm('cashup.change_tillclosure',
    is_staff_and_is_editable | is_tillclosure_outlet_owner)

rules.add_perm('cashup.view_tillclosure_audit_trail',
    is_tillclosure_outlet_manager | is_tillclosure_outlet_owner)
