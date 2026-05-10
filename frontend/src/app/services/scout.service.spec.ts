import { TestBed } from '@angular/core/testing';

import { ScoutService } from './scout.service';

describe('ScoutService', () => {
  let service: ScoutService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ScoutService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
