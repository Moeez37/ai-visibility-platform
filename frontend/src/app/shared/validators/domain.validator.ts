import { AbstractControl, ValidationErrors } from '@angular/forms';

const DOMAIN_PATTERN = /^(?!-)(?:[a-z0-9-]{1,63}\.)+[a-z]{2,}$/i;

export function isValidDomain(value: string): boolean {
  return DOMAIN_PATTERN.test(value.trim());
}

export function domainValidator(control: AbstractControl<string>): ValidationErrors | null {
  return !control.value || isValidDomain(control.value) ? null : { domain: true };
}
