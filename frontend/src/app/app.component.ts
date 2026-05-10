import { Component, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { StateService } from './services/state.service';
import { StreamService } from './services/stream.service';
import { InterviewComponent } from './components/interview/interview.component';
import { LoggerComponent } from './components/logger.component';
import { ReportComponent } from './components/report.component';
import { TimelineComponent } from './components/timeline.component';
import { HeaderComponent } from './components/header.component';
import { FooterComponent } from './components/footer.component';
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
    FooterComponent
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnDestroy {
  private state = inject(StateService);
  private stream = inject(StreamService);

  appState$ = this.state.appState$;
  private sub?: Subscription;

  readonly STRINGS = APP_STRINGS;
  readonly LINKS = PROJECT_LINKS;

  startInterview() {
    this.state.setAppState('INTERVIEW');
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }
}
