import { Component, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { StateService } from './services/state.service';
import { InterviewComponent } from './components/interview/interview.component';
import { LoggerComponent } from './components/logger.component';
import { ReportComponent } from './components/report.component';
import { TimelineComponent } from './components/timeline.component';
import { HeaderComponent } from './components/header.component';
import { FooterComponent } from './components/footer.component';
import { FactRotatorComponent } from './components/fact-rotator.component';
import { APP_STRINGS, PROJECT_LINKS } from '../constants';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, 
    InterviewComponent, 
    LoggerComponent, 
    ReportComponent, 
    TimelineComponent, 
    HeaderComponent,
    FooterComponent,
    FactRotatorComponent
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnDestroy {
  private state = inject(StateService);

  appState$     = this.state.appState$;
  traveledYear$ = this.state.traveledYear$;
  sidebarCollapsed = false;
  private sub?: Subscription;

  readonly STRINGS = APP_STRINGS;
  readonly LINKS = PROJECT_LINKS;

  startInterview() {
    this.state.setAppState('INTERVIEW');
  }

  getAgeAtTravel(year: number): number | null {
    if (!this.state.metrics.birthYear) return null;
    return year - this.state.metrics.birthYear;
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }
}
