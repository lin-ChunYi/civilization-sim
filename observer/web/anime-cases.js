/* anime-cases-1 contract for the observer UI. Match sample_id + kind + model identity. */
window.ANIME_CASES = {
  contract: "anime-cases-1",
  default_sample_id: "preset-anime-farm250",
  install: [
    "python3 -m observer.make_anime_cases",
    "OBSERVER_DATA_DIR=<空目录> python3 -m uvicorn observer.app:app --host 127.0.0.1 --port <空闲端口>",
  ],
  samples: [
    {
      sample_id: "preset-anime-farm250", tag: "A", engine: "exp07", farm_m: 250,
      model_run_id: "8d6281d91c14c3697d4390e8baca5fb9",
      full_digest: "8d6281d91c14c3697d4390e8baca5fb9/2a3e1ca14a83d53c17973ded56f85776",
      harvest_year: 2, harvest_event_id: "t2-farm_harvest-0",
      clear_year: 1, clear_event_id: "t1-field_built-0",
      migrate_year: 218, migrate_event_id: "t218-migrate-1",
      aid_year: 267, aid_event_id: "t267-aid-4",
      repay_year: 295, repay_event_id: "t295-aid-24",
    },
    {
      sample_id: "preset-anime-exp06", tag: "B", engine: "exp06", farm_m: null,
      model_run_id: "df1a9f4798463f545288f85ac096169b",
      full_digest: "df1a9f4798463f545288f85ac096169b/f80ebd6f1b7de72765cc3754ed227a74",
      farm: "engine_lacks_mechanism",
      migrate_year: 26, aid_year: 73, repay_year: 128,
    },
    {
      sample_id: "preset-anime-farm0", tag: "C", engine: "exp07", farm_m: 0,
      model_run_id: "112c9e1f580ac47710e8dc0c5ae0da17",
      full_digest: "112c9e1f580ac47710e8dc0c5ae0da17/ff6070addaae8847cf1e61dfa33a6c75",
      farm: "param_zero",
    },
    {
      sample_id: "preset-anime-farm1000", tag: "D", engine: "exp07", farm_m: 1000,
      model_run_id: "940cca8853e07c07c61dd4d1b1f77868",
      full_digest: "940cca8853e07c07c61dd4d1b1f77868/b1d6db9717a083d46e26526373cffb8e",
      farm: "abandonment",
    },
  ],
};
