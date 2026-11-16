# =============================================================================
#  TRANSLATIONS — English / French / Arabic
# =============================================================================

TRANSLATIONS = {
    'en': {
        # App
        'app_title':            'AgroAI — Smart Farming Assistant',
        'app_subtitle':         'Get the right crop and predict your yield with AI',
        'language':             'Language',

        # Steps
        'step1_title':          '1. Where is your farm?',
        'step1_help':           'Choose your country, then click on the map to mark your exact location',
        'step2_title':          '2. Soil & Climate Data',
        'step2_help':           'These values are loaded automatically. You can override them for testing.',
        'step3_title':          '3. Pesticides Used',
        'step4_title':          '4. Choose Year',
        'step5_title':          'Recommendations',

        # Sidebar
        'country':              'Country',
        'data_mode':            'Data Source',
        'data_auto':            'Auto (real-time IoT data)',
        'data_manual':          'Manual (test mode)',
        'fetch_data':           'Refresh Sensor Data',
        'pesticides':           'Pesticides used (tonnes)',
        'pesticides_help':      'Total pesticides applied per year',

        # Soil
        'soil_section':         'Soil Properties (auto-detected)',
        'nitrogen':             'Nitrogen (N)',
        'phosphorus':           'Phosphorus (P)',
        'potassium':            'Potassium (K)',
        'soil_ph':              'Soil pH',

        # Weather (IoT)
        'weather_section':      'Weather (IoT sensors)',
        'temperature':          'Temperature',
        'humidity':             'Humidity',
        'rainfall':             'Rainfall',
        'wind':                 'Wind speed',

        # Map
        'map_instruction':      'Click anywhere on the map to select your farm location',
        'map_selected':         'Selected location',
        'lat':                  'Latitude',
        'lon':                  'Longitude',

        # Predict
        'predict_btn':          'Get My Recommendation',
        'predicting':           'Analyzing your farm data...',
        'select_location_first': 'Please click on the map to select your farm location first',

        # Results
        'recommended_crop':     'Recommended Crop',
        'expected_yield':       'Expected Yield',
        'this_year':            'This year',
        'next_5_years':         'Yield forecast — Next 5 years',
        'forecast_help':        'AI-predicted yield trend for your farm',
        'tons_per_hectare':     'tonnes / hectare',
        'kg_per_hectare':       'kg / hectare',
        'best_year':            'Best year',
        'avg_yield':            'Average yield',

        # Year
        'year_select':          'Year for prediction',

        # Status
        'data_source':          'Data source',
        'live_iot':             'Live IoT sensors',
        'manual_test':          'Manual test mode',
        'api_failed':           'Could not reach API — using estimated values',

        # Tips
        'tips_title':           'Farming Tips',
        'tip_planting':         'Best planting time',
        'tip_water':             'Water requirement',
        'tip_soil':              'Soil suitability',

        # Footer
        'powered_by':           'Powered by AI · Real-time IoT data · SoilGrids + Open-Meteo APIs',

        # Misc
        'click_map_first':      '👆 Click on the map to select your farm location',
        'crop_mapping_note':    'Note: yield estimated using a similar crop from our database',
        'low':   'Low',  'medium': 'Medium', 'high': 'High', 'optimal': 'Optimal',
    },

    'fr': {
        'app_title':            'AgroAI — Assistant de Culture Intelligent',
        'app_subtitle':         "Trouvez la culture idéale et prédisez votre rendement avec l'IA",
        'language':             'Langue',

        'step1_title':          '1. Où se trouve votre ferme ?',
        'step1_help':           'Choisissez votre pays, puis cliquez sur la carte pour marquer votre emplacement exact',
        'step2_title':          '2. Données du sol et du climat',
        'step2_help':           'Ces valeurs sont chargées automatiquement. Vous pouvez les modifier pour tester.',
        'step3_title':          '3. Pesticides Utilisés',
        'step4_title':          '4. Choisir l\'année',
        'step5_title':          'Recommandations',

        'country':              'Pays',
        'data_mode':            'Source de données',
        'data_auto':            'Auto (données IoT en temps réel)',
        'data_manual':          'Manuel (mode test)',
        'fetch_data':           'Actualiser les capteurs',
        'pesticides':           'Pesticides utilisés (tonnes)',
        'pesticides_help':      'Total des pesticides appliqués par an',

        'soil_section':         'Propriétés du sol (auto-détecté)',
        'nitrogen':             'Azote (N)',
        'phosphorus':           'Phosphore (P)',
        'potassium':            'Potassium (K)',
        'soil_ph':              'pH du sol',

        'weather_section':      'Météo (capteurs IoT)',
        'temperature':          'Température',
        'humidity':             'Humidité',
        'rainfall':             'Précipitations',
        'wind':                 'Vitesse du vent',

        'map_instruction':      'Cliquez sur la carte pour sélectionner votre ferme',
        'map_selected':         'Emplacement sélectionné',
        'lat':                  'Latitude',
        'lon':                  'Longitude',

        'predict_btn':          'Obtenir ma recommandation',
        'predicting':           'Analyse de votre ferme en cours...',
        'select_location_first': 'Veuillez d\'abord cliquer sur la carte pour sélectionner votre ferme',

        'recommended_crop':     'Culture Recommandée',
        'expected_yield':       'Rendement Attendu',
        'this_year':            'Cette année',
        'next_5_years':         'Prévisions — 5 prochaines années',
        'forecast_help':        'Tendance du rendement prédite par IA',
        'tons_per_hectare':     'tonnes / hectare',
        'kg_per_hectare':       'kg / hectare',
        'best_year':            'Meilleure année',
        'avg_yield':            'Rendement moyen',

        'year_select':          'Année de prédiction',

        'data_source':          'Source des données',
        'live_iot':             'Capteurs IoT en direct',
        'manual_test':          'Mode test manuel',
        'api_failed':           'API inaccessible — valeurs estimées',

        'tips_title':           'Conseils Agricoles',
        'tip_planting':         'Meilleure période de plantation',
        'tip_water':            'Besoins en eau',
        'tip_soil':             'Adaptabilité du sol',

        'powered_by':           'Propulsé par IA · Données IoT en direct · APIs SoilGrids + Open-Meteo',

        'click_map_first':      '👆 Cliquez sur la carte pour sélectionner votre ferme',
        'crop_mapping_note':    'Note : rendement estimé via une culture similaire de notre base',
        'low':   'Faible',  'medium': 'Moyen', 'high': 'Élevé', 'optimal': 'Optimal',
    },

    'ar': {
        'app_title':            'أغرو AI — مساعد الزراعة الذكي',
        'app_subtitle':         'اعثر على المحصول الأمثل وتوقع إنتاجيتك بمساعدة الذكاء الاصطناعي',
        'language':             'اللغة',

        'step1_title':          '١. أين توجد مزرعتك؟',
        'step1_help':           'اختر بلدك ثم انقر على الخريطة لتحديد موقعك بدقة',
        'step2_title':          '٢. بيانات التربة والمناخ',
        'step2_help':           'يتم تحميل هذه القيم تلقائيًا. يمكنك تعديلها للاختبار.',
        'step3_title':          '٣. المبيدات المستخدمة',
        'step4_title':          '٤. اختر السنة',
        'step5_title':          'التوصيات',

        'country':              'البلد',
        'data_mode':            'مصدر البيانات',
        'data_auto':            'تلقائي (بيانات IoT مباشرة)',
        'data_manual':          'يدوي (وضع الاختبار)',
        'fetch_data':           'تحديث المستشعرات',
        'pesticides':           'المبيدات المستخدمة (طن)',
        'pesticides_help':      'إجمالي المبيدات المستخدمة سنويًا',

        'soil_section':         'خصائص التربة (تلقائي)',
        'nitrogen':             'النيتروجين (N)',
        'phosphorus':           'الفوسفور (P)',
        'potassium':            'البوتاسيوم (K)',
        'soil_ph':              'حموضة التربة',

        'weather_section':      'الطقس (مستشعرات IoT)',
        'temperature':          'درجة الحرارة',
        'humidity':             'الرطوبة',
        'rainfall':             'الأمطار',
        'wind':                 'سرعة الرياح',

        'map_instruction':      'انقر على الخريطة لتحديد موقع مزرعتك',
        'map_selected':         'الموقع المحدد',
        'lat':                  'خط العرض',
        'lon':                  'خط الطول',

        'predict_btn':          'احصل على توصيتي',
        'predicting':           'جاري تحليل بيانات مزرعتك...',
        'select_location_first': 'يرجى النقر على الخريطة لتحديد موقع مزرعتك أولاً',

        'recommended_crop':     'المحصول الموصى به',
        'expected_yield':       'الإنتاجية المتوقعة',
        'this_year':            'هذه السنة',
        'next_5_years':         'توقعات الإنتاجية — السنوات الخمس القادمة',
        'forecast_help':        'اتجاه الإنتاجية المتوقع بواسطة الذكاء الاصطناعي',
        'tons_per_hectare':     'طن / هكتار',
        'kg_per_hectare':       'كغ / هكتار',
        'best_year':            'أفضل سنة',
        'avg_yield':            'متوسط الإنتاجية',

        'year_select':          'سنة التنبؤ',

        'data_source':          'مصدر البيانات',
        'live_iot':             'مستشعرات IoT مباشرة',
        'manual_test':          'وضع الاختبار اليدوي',
        'api_failed':           'تعذر الوصول إلى API — قيم تقديرية',

        'tips_title':           'نصائح زراعية',
        'tip_planting':         'أفضل موعد للزراعة',
        'tip_water':            'احتياجات المياه',
        'tip_soil':             'ملاءمة التربة',

        'powered_by':           'مدعوم بالذكاء الاصطناعي · بيانات IoT مباشرة · APIs SoilGrids + Open-Meteo',

        'click_map_first':      '👆 انقر على الخريطة لتحديد موقع مزرعتك',
        'crop_mapping_note':    'ملاحظة: تم تقدير الإنتاجية باستخدام محصول مشابه من قاعدة بياناتنا',
        'low':   'منخفض', 'medium': 'متوسط', 'high': 'مرتفع', 'optimal': 'مثالي',
    },
}


def t(key: str, lang: str = 'en') -> str:
    """Translate a key to the given language."""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(
        key, TRANSLATIONS['en'].get(key, key)
    )


def get_text_direction(lang: str) -> str:
    """Returns 'rtl' for Arabic, 'ltr' otherwise."""
    return 'rtl' if lang == 'ar' else 'ltr'


# Crop name translations (kept simple — just main crops)
CROP_NAMES = {
    'rice':        {'en': 'Rice',         'fr': 'Riz',         'ar': 'الأرز'},
    'maize':       {'en': 'Maize',        'fr': 'Maïs',        'ar': 'الذرة'},
    'wheat':       {'en': 'Wheat',        'fr': 'Blé',         'ar': 'القمح'},
    'potato':      {'en': 'Potato',       'fr': 'Pomme de terre', 'ar': 'البطاطا'},
    'banana':      {'en': 'Banana',       'fr': 'Banane',      'ar': 'الموز'},
    'mango':       {'en': 'Mango',        'fr': 'Mangue',      'ar': 'المانجو'},
    'apple':       {'en': 'Apple',        'fr': 'Pomme',       'ar': 'التفاح'},
    'orange':      {'en': 'Orange',       'fr': 'Orange',      'ar': 'البرتقال'},
    'grapes':      {'en': 'Grapes',       'fr': 'Raisins',     'ar': 'العنب'},
    'watermelon':  {'en': 'Watermelon',   'fr': 'Pastèque',    'ar': 'البطيخ'},
    'muskmelon':   {'en': 'Muskmelon',    'fr': 'Melon',       'ar': 'الشمام'},
    'papaya':      {'en': 'Papaya',       'fr': 'Papaye',      'ar': 'البابايا'},
    'coconut':     {'en': 'Coconut',      'fr': 'Noix de coco', 'ar': 'جوز الهند'},
    'cotton':      {'en': 'Cotton',       'fr': 'Coton',       'ar': 'القطن'},
    'jute':        {'en': 'Jute',         'fr': 'Jute',        'ar': 'الجوت'},
    'coffee':      {'en': 'Coffee',       'fr': 'Café',        'ar': 'القهوة'},
    'sugarcane':   {'en': 'Sugarcane',    'fr': 'Canne à sucre', 'ar': 'قصب السكر'},
    'tomato':      {'en': 'Tomato',       'fr': 'Tomate',      'ar': 'الطماطم'},
    'pomegranate': {'en': 'Pomegranate',  'fr': 'Grenade',     'ar': 'الرمان'},
    'chickpea':    {'en': 'Chickpea',     'fr': 'Pois chiche', 'ar': 'الحمص'},
    'kidneybeans': {'en': 'Kidney beans', 'fr': 'Haricots rouges', 'ar': 'الفاصوليا'},
    'pigeonpeas':  {'en': 'Pigeon peas',  'fr': 'Pois d\'Angole', 'ar': 'البازلاء'},
    'mothbeans':   {'en': 'Moth beans',   'fr': 'Haricots Moth', 'ar': 'فول الفراشة'},
    'mungbean':    {'en': 'Mung bean',    'fr': 'Haricot mungo', 'ar': 'فول المونغ'},
    'blackgram':   {'en': 'Black gram',   'fr': 'Lentille noire', 'ar': 'العدس الأسود'},
    'lentil':      {'en': 'Lentil',       'fr': 'Lentille',    'ar': 'العدس'},
}


def translate_crop(crop_name: str, lang: str = 'en') -> str:
    """Translate a crop name. Falls back to capitalize if not found."""
    crop_lower = crop_name.lower().strip()
    if crop_lower in CROP_NAMES:
        return CROP_NAMES[crop_lower].get(lang, crop_name.capitalize())
    return crop_name.capitalize()
