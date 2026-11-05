import { COMMA, ENTER } from '@angular/cdk/keycodes';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatChipInputEvent, MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router, RouterLink } from '@angular/router';

import { NotificationService } from '../../../core/services/notification.service';
import { ProfileService } from '../../../core/services/profile.service';
import { domainValidator, isValidDomain } from '../../../shared/validators/domain.validator';

const MAX_COMPETITORS = 20;

@Component({
  selector: 'app-profile-form',
  imports: [
    MatButtonModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    ReactiveFormsModule,
    RouterLink,
  ],
  templateUrl: './profile-form.component.html',
  styleUrl: './profile-form.component.scss',
})
export class ProfileFormComponent {
  private readonly profileService = inject(ProfileService);
  private readonly notifications = inject(NotificationService);
  private readonly router = inject(Router);

  protected readonly separatorKeys = [ENTER, COMMA];
  protected readonly submitting = signal(false);
  protected readonly competitorError = signal<string | null>(null);

  protected readonly form = inject(FormBuilder).nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(255)]],
    domain: ['', [Validators.required, domainValidator]],
    industry: ['', [Validators.required, Validators.maxLength(255)]],
    description: ['', Validators.required],
    competitors: [[] as string[]],
  });

  protected addCompetitor(event: MatChipInputEvent): void {
    const value = event.value.trim().toLowerCase();
    const current = this.form.controls.competitors.value;
    if (!value) {
      return;
    }
    if (!isValidDomain(value)) {
      this.competitorError.set(`"${value}" isn't a bare domain. Use a format like competitor.com.`);
      return;
    }
    if (current.includes(value)) {
      this.competitorError.set(`${value} is already in the list.`);
      return;
    }
    if (current.length >= MAX_COMPETITORS) {
      this.competitorError.set(`You can add up to ${MAX_COMPETITORS} competitors.`);
      return;
    }
    this.form.controls.competitors.setValue([...current, value]);
    this.competitorError.set(null);
    event.chipInput.clear();
  }

  protected removeCompetitor(competitor: string): void {
    const current = this.form.controls.competitors.value;
    this.form.controls.competitors.setValue(current.filter((item) => item !== competitor));
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.profileService.create(this.form.getRawValue()).subscribe({
      next: (profile) => {
        this.notifications.success(`${profile.name} added.`);
        void this.router.navigate(['/profiles', profile.profile_uuid]);
      },
      error: (error: Error) => {
        this.submitting.set(false);
        this.notifications.error(error.message);
      },
    });
  }
}
