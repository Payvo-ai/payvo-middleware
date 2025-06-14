"""
Comprehensive MCC Categories Utility
Complete Stripe Issuing MCC category mappings for all business types
"""

# Complete Stripe Issuing MCC Categories Mapping
MCC_CATEGORIES = {
    # Food & Dining
    "restaurant": "5812", "eating": "5812", "dining": "5812", "food": "5812", "eatery": "5812",
    "fast_food": "5814", "quick_service": "5814", "fast_casual": "5814", "drive_through": "5814",
    "coffee": "5462", "cafe": "5462", "bakery": "5462", "pastry": "5462", "tea": "5462",
    "bar": "5921", "pub": "5921", "brewery": "5921", "nightclub": "5921", "cocktail": "5921",
    "caterer": "5811", "catering": "5811",
    
    # Agriculture & Farming
    "farm": "0763", "agriculture": "0763", "agricultural": "0763", "farming": "0763", "ranch": "0763",
    "veterinary": "0742", "animal_hospital": "0742", "pet_clinic": "0742", "vet": "0742",
    "landscaping": "0780", "lawn_care": "0780", "garden_service": "0780", "groundskeeping": "0780",
    
    # Construction & Contractors
    "construction": "1520", "general_contractor": "1520", "builder": "1520", "building_contractor": "1520",
    "carpentry": "1750", "carpenter": "1750", "woodwork": "1750", "cabinet": "1750",
    "concrete": "1771", "cement": "1771", "masonry": "1771", "stonework": "1771",
    "electrical": "1731", "electrician": "1731", "electric": "1731", "wiring": "1731",
    "glass": "1740", "glazing": "1740", "window_installation": "1740",
    "heating": "1711", "hvac": "1711", "air_conditioning": "1711", "cooling": "1711", "ventilation": "1711", "plumbing": "1711", "plumber": "1711",
    "insulation": "1799", "weatherproofing": "1799",
    "painting": "1721", "painter": "1721", "decorating": "1721", "wallpaper": "1721",
    "roofing": "1761", "roofer": "1761", "siding": "1761", "gutters": "1761",
    "welding": "7692", "welder": "7692", "metal_fabrication": "7692",
    
    # Manufacturing & Wholesale
    "chemical": "5169", "industrial": "5169", "chemicals": "5169", "laboratory_supply": "5169",
    "commercial_equipment": "5046", "industrial_equipment": "5046",
    "computer_wholesale": "5045", "tech_wholesale": "5045", "electronics_wholesale": "5045",
    "construction_materials": "5039", "building_materials_wholesale": "5039",
    "drug_wholesale": "5122", "pharmaceutical_wholesale": "5122", "medical_wholesale": "5122",
    "electrical_parts": "5065", "electrical_wholesale": "5065",
    "footwear_wholesale": "5139", "shoe_wholesale": "5139",
    "furniture_wholesale": "5021", "office_furniture_wholesale": "5021",
    "hardware_wholesale": "5072", "tools_wholesale": "5072",
    "jewelry_wholesale": "5094", "watch_wholesale": "5094",
    "lumber": "5211", "building_supplies": "5211", "timber": "5211",
    "metals": "5051", "steel": "5051", "metal_service": "5051",
    "office_supplies_wholesale": "5111", "stationery_wholesale": "5111",
    "paint_wholesale": "5198", "coating_wholesale": "5198",
    "paper": "5111", "paper_products": "5111", "packaging_materials": "5111",
    "petroleum_wholesale": "5172", "fuel_wholesale": "5172",
    "photographic_wholesale": "5044", "camera_wholesale": "5044",
    "plumbing_wholesale": "5074", "heating_wholesale": "5074",
    "textile_wholesale": "5131", "fabric_wholesale": "5131",
    "tobacco_wholesale": "5194", "cigarette_wholesale": "5194",
    "book_wholesale": "5192", "publishing": "5192", "publisher": "5192",
    "printing": "2791", "typesetting": "2791", "print_shop": "2791",
    "newspaper": "5192", "magazine": "5192", "periodical": "5192",
    
    # Retail
    "gas_station": "5541", "petrol_station": "5541", "fuel_station": "5541",
    "automated_fuel": "5542", "self_service_fuel": "5542",
    "grocery": "5411", "supermarket": "5411", "market": "5411", "food_store": "5411",
    "convenience": "5499", "corner_store": "5499", "mini_mart": "5499",
    "candy": "5441", "confectionery": "5441", "sweets": "5441", "chocolate": "5441",
    "clothing": "5651", "apparel": "5651", "fashion": "5651",
    "mens_clothing": "5611", "menswear": "5611",
    "womens_clothing": "5621", "ladies_wear": "5621",
    "childrens_clothing": "5641", "kids_clothes": "5641", "baby_clothes": "5641",
    "womens_accessories": "5631", "handbags": "5631", "purses": "5631",
    "sports_apparel": "5655", "athletic_wear": "5655", "sportswear": "5655",
    "uniform": "5137", "work_clothes": "5137",
    "shoe_store": "5661", "footwear": "5661", "boots": "5661", "sneakers": "5661",
    "electronics": "5732", "computer": "5732", "tech_store": "5732",
    "computer_software": "5734", "software_store": "5734",
    "record_store": "5735", "music_store": "5735", "vinyl": "5735",
    "department_store": "5311", "retail_chain": "5311",
    "discount_store": "5310", "dollar_store": "5310",
    "variety_store": "5331", "general_store": "5331",
    "wholesale_club": "5300", "membership_store": "5300",
    "pharmacy": "5912", "drugstore": "5912", "chemist": "5912",
    "furniture": "5712", "home_furnishing": "5712",
    "home_improvement": "5200", "home_depot": "5200", "hardware_superstore": "5200",
    "appliance": "5722", "kitchen_appliances": "5722",
    "jewelry": "5944", "jeweler": "5944", "watches": "5944",
    "book_store": "5942", "bookshop": "5942", "library_store": "5942",
    "stationery": "5943", "office_supply": "5943", "school_supplies": "5943",
    "sporting_goods": "5941", "sports_equipment": "5941", "outdoor_gear": "5941",
    "toy_store": "5945", "hobby": "5945", "games": "5945",
    "camera_store": "5946", "photography_equipment": "5946",
    "gift_shop": "5947", "novelty": "5947", "souvenir": "5947",
    "fabric": "5949", "sewing": "5949", "needlework": "5949",
    "hardware_store": "5251", "tools": "5251", "home_repair": "5251",
    "paint_store": "5231", "wallpaper": "5231", "decorating_supplies": "5231",
    "lumber_yard": "5211", "building_materials": "5211",
    "nursery": "5261", "garden_center": "5261", "plants": "5261",
    "pet_store": "5995", "pet_supplies": "5995", "pet_food": "5995",
    "florist": "5992", "flower_shop": "5992", "flowers": "5992",
    "bicycle": "5940", "bike_store": "5940", "cycling": "5940",
    "motorcycle": "5571", "bike_dealer": "5571", "scooter": "5571",
    "boat": "5551", "marine": "5551", "yacht": "5551",
    "rv": "5561", "recreational_vehicle": "5561", "camper": "5561",
    "snowmobile": "5598", "winter_sports": "5598",
    "art": "5971", "gallery": "5971", "fine_art": "5971",
    "artist_supply": "5970", "craft": "5970", "art_materials": "5970",
    "antique": "5932", "antiques": "5932", "collectibles": "5932",
    "antique_reproduction": "5937", "replica": "5937",
    "used_goods": "5931", "secondhand": "5931", "consignment": "5931",
    "pawn": "5933", "pawnbroker": "5933",
    "cigar": "5993", "tobacco": "5993", "smoking": "5993",
    "cosmetic": "5977", "beauty_products": "5977", "makeup": "5977",
    "typewriter": "5978", "office_machines": "5978",
    "wig": "5698", "hair_pieces": "5698", "toupee": "5698",
    "religious_goods": "5973", "church_supplies": "5973",
    "stamp": "5972", "coin": "5972", "collectible_currency": "5972",
    "orthopedic": "5976", "prosthetic": "5976", "medical_devices": "5976",
    "optical": "5976", "eyeglasses": "5976", "contacts": "5976",
    "tent": "5998", "awning": "5998", "outdoor_shelter": "5998",
    "swimming_pool": "5996", "pool_supplies": "5996",
    "retail": "5999", "miscellaneous_retail": "5999", "general_retail": "5999",
    
    # Automotive
    "automotive": "5511", "car_dealer": "5511", "auto_dealer": "5511", "vehicle_sales": "5511",
    "used_car": "5521", "pre_owned_vehicles": "5521",
    "tire": "5532", "tire_store": "5532", "wheels": "5532",
    "auto_parts": "5533", "car_parts": "5533", "automotive_accessories": "5533",
    "auto_supply": "5531", "automotive_supply": "5531",
    "car_rental": "7512", "vehicle_rental": "7512", "rent_a_car": "7512",
    "truck_rental": "7513", "van_rental": "7513", "moving_truck": "7513",
    "rv_rental": "7519", "camper_rental": "7519",
    "auto_body": "7531", "collision_repair": "7531", "dent_repair": "7531",
    "tire_repair": "7534", "tire_service": "7534",
    "auto_paint": "7535", "car_painting": "7535",
    "auto_repair": "7538", "car_service": "7538", "mechanic": "7538",
    "car_wash": "7542", "auto_wash": "7542", "detailing": "7542",
    "towing": "7549", "roadside_assistance": "7549",
    
    # Financial Services
    "bank": "6011", "atm": "6011", "financial_institution": "6011",
    "quasi_cash": "6051", "cash_advance": "6051",
    "credit_union": "6012", "savings_bank": "6012",
    "credit_reporting": "7321", "credit_bureau": "7321",
    "collection": "7322", "debt_collection": "7322",
    "debt_counseling": "7299", "financial_counseling": "7299",
    "check_cashing": "6051", "money_services": "6051",
    "money_order": "4829", "wire_transfer": "4829",
    "security_broker": "6211", "investment": "6211", "stock_broker": "6211",
    "insurance": "6300", "insurance_agent": "6300", "coverage": "6300",
    "real_estate": "6513", "property_management": "6513", "realtor": "6513",
    
    # Lodging & Travel
    "hotel": "7011", "motel": "7011", "resort": "7011", "inn": "7011",
    "timeshare": "7012", "vacation_rental": "7012",
    "campground": "7033", "camping": "7033", "rv_park": "7033",
    "sporting_camp": "7032", "adventure_camp": "7032",
    "travel_agency": "4722", "tour_operator": "4722", "travel_service": "4722",
    "tui_travel": "4723", "vacation_package": "4723",
    
    # Health & Medical
    "hospital": "8062", "medical_center": "8062", "clinic": "8062", "healthcare": "8062",
    "doctor": "8011", "physician": "8011", "medical_doctor": "8011",
    "dentist": "8021", "dental": "8021", "orthodontist": "8021",
    "osteopath": "8031", "osteopathic": "8031",
    "chiropractor": "8041", "chiropractic": "8041",
    "optometrist": "8042", "eye_doctor": "8042", "ophthalmologist": "8042",
    "optician": "8043", "eyeglasses": "8043", "optical": "8043",
    "podiatrist": "8049", "foot_doctor": "8049", "chiropodist": "8049",
    "nursing_home": "8050", "personal_care": "8050", "elderly_care": "8050",
    "ambulance": "4119",
    "blood": "8071", "lab": "8071",
    "mental_health": "8031", "psychiatrist": "8031", "therapist": "8031",
    
    # Beauty & Personal Care
    "salon": "7230", "spa": "7230", "beauty": "7230", "barber": "7230", "hair": "7230",
    "nail": "7230", "manicure": "7230", "pedicure": "7230",
    "massage": "7298",
    "laundry": "7216", "dry_clean": "7216",
    "tailor": "5697", "alteration": "5697",
    
    # Fitness & Recreation
    "gym": "7997", "fitness": "7997", "health_club": "7997", "yoga": "7997",
    "pool": "7997", "swimming": "7997",
    "tennis": "7997", "court": "7997",
    "golf": "7997", "country_club": "7997",
    "bowling": "7933",
    "billiard": "7932", "pool_hall": "7932",
    "recreation": "7032", "camp": "7032",
    
    # Entertainment & Recreation
    "movie": "7832", "cinema": "7832", "theater": "7832", "theatre": "7832",
    "park": "7996", "amusement": "7996",
    "casino": "7995", "gambling": "7995", "gaming": "7995",
    "arcade": "7994",
    "aquarium": "7998",
    "zoo": "7998",
    "museum": "7991",
    "band": "7929", "orchestra": "7929", "music": "7929",
    "ticket": "7922", "event": "7922",
    
    # Transportation
    "taxi": "4121", "cab": "4121", "uber": "4121", "lyft": "4121",
    "bus": "4131", "transit": "4131",
    "train": "4112", "railway": "4112",
    "airline": "4511", "airport": "4511",
    "ferry": "4111", "boat": "4111",
    "parking": "7523", "garage": "7523",
    "toll": "4784", "bridge": "4784",
    "transportation": "4111",
    
    # Professional Services
    "lawyer": "8111", "attorney": "8111", "legal_service": "8111",
    "accountant": "8931", "bookkeeping": "8931", "tax_service": "8931",
    "advertising": "7311", "marketing": "7311", "ad_agency": "7311",
    "consultant": "7392", "consulting": "7392", "public_relations": "7392",
    "courier": "4215", "delivery": "4215",
    "cleaning": "7349", "maintenance": "7349",
    "security": "7382",
    "photography": "7221", "photographer": "7221",
    "copy": "7338",
    "employment": "7361", "staffing": "7361",
    "architect": "8911", "architectural": "8911", "surveying": "8911",
    "engineering": "8911",
    
    # Education
    "university": "8220", "college": "8220", "higher_education": "8220",
    "elementary": "8211", "primary": "8211",
    "childcare": "8351", "daycare": "8351",
    "driving_school": "8299",
    "dance": "8299", "music_lesson": "8299",
    "vocational": "8249", "trade_school": "8249",
    "school": "8220",
    
    # Government & Public Services
    "post_office": "9402", "postal_service": "9402",
    "courthouse": "9211", "court": "9211",
    "city_hall": "9399", "government": "9399",
    "library": "8231",
    "police": "9399", "fire_department": "9399",
    "dmv": "9399", "motor_vehicle": "9399",
    
    # Religious & Charitable
    "church": "8661", "mosque": "8661", "synagogue": "8661", "temple": "8661", "religious": "8661",
    "charity": "8398", "charitable": "8398", "fundraising": "8398",
    
    # Utilities & Communication
    "utility": "4900", "electric": "4900", "water": "4900",
    "telephone": "4814", "telecom": "4814",
    "internet": "4899", "cable": "4899",
    
    # Specialty Services
    "buying_service": "7278",
    "counseling": "7277",
    "dating_service": "7273",
    "diet_service": "7299",
    "drug_treatment": "8093",
    "funeral": "7261",
    "marriage_counseling": "7277",
    "tax_preparation": "7276",
    "testing_lab": "8734",
    "quick_copy": "7338", "blueprint": "7338"
}

# Google Places types to MCC mapping - comprehensive coverage using full Stripe categories
GOOGLE_PLACES_TO_MCC = {
    # Food & Dining - comprehensive Google Places food types
    "restaurant": "5812", "meal_takeaway": "5814", "meal_delivery": "5814",
    "bakery": "5462", "cafe": "5462", "coffee_shop": "5462",
    "bar": "5921", "night_club": "5921", "liquor_store": "5921",
    "food": "5812", "fast_food": "5814", "pizza": "5812",
    
    # Retail - comprehensive Google Places retail types
    "gas_station": "5541", "grocery_or_supermarket": "5411", "supermarket": "5411",
    "convenience_store": "5499", "clothing_store": "5651", "shoe_store": "5661",
    "electronics_store": "5732", "furniture_store": "5712", "home_goods_store": "5712",
    "hardware_store": "5251", "book_store": "5942", "jewelry_store": "5944",
    "pet_store": "5995", "florist": "5992", "bicycle_store": "5940",
    "car_dealer": "5511", "department_store": "5311", "shopping_mall": "5311",
    "store": "5999", "pharmacy": "5912", "drugstore": "5912",
    
    # Automotive - comprehensive Google Places automotive types
    "car_rental": "7512", "car_repair": "7538", "car_wash": "7542",
    "auto_parts_store": "5533", "tire_shop": "5532", "auto_body_shop": "7531",
    "motorcycle_dealer": "5571", "boat_dealer": "5551", "rv_dealer": "5561",
    
    # Health & Medical - comprehensive Google Places health types
    "hospital": "8062", "doctor": "8011", "dentist": "8021", "dental_office": "8021",
    "veterinary_care": "0742", "clinic": "8062", "medical_office": "8011",
    "optometrist": "8042", "physiotherapist": "8049", "chiropractor": "8041",
    "mental_health": "8031", "nursing_home": "8050",
    
    # Services - comprehensive Google Places service types
    "bank": "6011", "atm": "6011", "insurance_agency": "6300",
    "real_estate_agency": "6513", "lawyer": "8111", "accounting": "8931",
    "travel_agency": "4722", "moving_company": "4214", "storage": "4225",
    "post_office": "9402", "courier": "4215", "dry_cleaning": "7216",
    "laundry": "7216", "locksmith": "7699", "funeral_home": "7261",
    
    # Beauty & Personal Care - comprehensive Google Places beauty types
    "beauty_salon": "7230", "hair_care": "7230", "spa": "7230",
    "nail_salon": "7230", "barber_shop": "7230", "massage": "7298",
    
    # Entertainment & Recreation - comprehensive Google Places entertainment types
    "movie_theater": "7832", "amusement_park": "7996", "bowling_alley": "7933",
    "casino": "7995", "gym": "7997", "fitness_center": "7997",
    "tourist_attraction": "7996", "zoo": "7998", "aquarium": "7998",
    "museum": "7991", "art_gallery": "5971", "library": "8231",
    "stadium": "7922", "golf_course": "7997", "tennis_court": "7997",
    "swimming_pool": "7997", "campground": "7033", "park": "7996",
    
    # Lodging - comprehensive Google Places lodging types
    "lodging": "7011", "hotel": "7011", "motel": "7011", "resort": "7011",
    "bed_and_breakfast": "7011", "hostel": "7011", "rv_park": "7033",
    
    # Transportation - comprehensive Google Places transportation types
    "taxi_stand": "4121", "bus_station": "4131", "train_station": "4112",
    "airport": "4511", "subway_station": "4111", "parking": "7523",
    "gas_station": "5541", "ferry_terminal": "4111",
    
    # Education & Government - comprehensive Google Places institutional types
    "school": "8220", "university": "8220", "college": "8220",
    "primary_school": "8211", "secondary_school": "8211",
    "city_hall": "9399", "courthouse": "9211", "police": "9399",
    "fire_station": "9399", "embassy": "9399", "local_government_office": "9399",
    
    # Religious - comprehensive Google Places religious types
    "church": "8661", "hindu_temple": "8661", "mosque": "8661",
    "synagogue": "8661", "place_of_worship": "8661", "cemetery": "7261",
    
    # Construction & Professional Services
    "electrician": "1731", "plumber": "1711", "contractor": "1520",
    "painter": "1721", "roofing_contractor": "1761", "carpenter": "1750",
    "landscaper": "0780", "architect": "8911", "engineer": "8911",
    
    # Specialized Services
    "veterinarian": "0742", "farm": "0763", "agricultural_supply": "0763",
    "printing_service": "2791", "advertising_agency": "7311",
    "employment_agency": "7361", "security_service": "7382",
    "cleaning_service": "7349", "pest_control": "7342"
}

# Foursquare category patterns - comprehensive coverage using full Stripe categories
FOURSQUARE_CATEGORY_PATTERNS = {
    # Food & Dining patterns - comprehensive Foursquare food categories
    "restaurant": "5812", "diner": "5812", "bistro": "5812", "brasserie": "5812",
    "fast_food": "5814", "quick_service": "5814", "fast_casual": "5814", "drive_thru": "5814",
    "coffee": "5462", "cafe": "5462", "bakery": "5462", "donut": "5462", "tea": "5462",
    "bar": "5921", "pub": "5921", "brewery": "5921", "nightlife": "5921", "cocktail": "5921",
    "pizza": "5812", "burger": "5814", "sandwich": "5814", "taco": "5814", "sushi": "5812",
    "steakhouse": "5812", "seafood": "5812", "chinese": "5812", "italian": "5812",
    "mexican": "5812", "thai": "5812", "indian": "5812", "japanese": "5812",
    "mediterranean": "5812", "american": "5812", "french": "5812", "korean": "5812",
    "ice_cream": "5814", "frozen_yogurt": "5814", "dessert": "5814", "candy": "5441",
    "wine_bar": "5921", "sports_bar": "5921", "lounge": "5921", "club": "5921",
    
    # Retail patterns - comprehensive Foursquare retail categories
    "shop": "5999", "store": "5999", "retail": "5999", "boutique": "5999",
    "grocery": "5411", "supermarket": "5411", "market": "5411", "organic": "5411",
    "convenience": "5499", "corner_store": "5499", "mini_mart": "5499",
    "gas": "5541", "petrol": "5541", "fuel": "5541", "service_station": "5541",
    "clothing": "5651", "fashion": "5651", "apparel": "5651", "vintage": "5651",
    "shoe": "5661", "footwear": "5661", "sneaker": "5661", "boot": "5661",
    "electronics": "5732", "computer": "5732", "tech": "5732", "mobile": "5732",
    "furniture": "5712", "home": "5712", "decor": "5712", "antique": "5932",
    "hardware": "5251", "tools": "5251", "home_improvement": "5200",
    "book": "5942", "bookstore": "5942", "library": "8231",
    "jewelry": "5944", "watch": "5944", "accessories": "5944",
    "pet": "5995", "animal": "5995", "veterinary": "0742",
    "flower": "5992", "florist": "5992", "garden": "5261", "nursery": "5261",
    "bike": "5940", "bicycle": "5940", "cycling": "5940",
    "auto": "5511", "car": "5511", "motorcycle": "5571", "boat": "5551",
    "pharmacy": "5912", "drugstore": "5912", "health": "5912",
    "sporting_goods": "5941", "sports": "5941", "outdoor": "5941", "camping": "5941",
    "toy": "5945", "game": "5945", "hobby": "5945", "craft": "5970",
    "music": "5735", "record": "5735", "instrument": "5735",
    "camera": "5946", "photo": "5946", "photography": "5946",
    "gift": "5947", "souvenir": "5947", "novelty": "5947",
    "cosmetic": "5977", "beauty": "5977", "makeup": "5977",
    
    # Services patterns - comprehensive Foursquare service categories
    "bank": "6011", "financial": "6011", "atm": "6011", "credit_union": "6012",
    "insurance": "6300", "real_estate": "6513", "investment": "6211",
    "hotel": "7011", "motel": "7011", "inn": "7011", "resort": "7011",
    "bed_breakfast": "7011", "hostel": "7011", "vacation_rental": "7012",
    "hospital": "8062", "clinic": "8062", "medical": "8062", "emergency": "8062",
    "doctor": "8011", "physician": "8011", "dentist": "8021", "dental": "8021",
    "optometrist": "8042", "eye_care": "8042", "chiropractor": "8041",
    "mental_health": "8031", "therapy": "8031", "counseling": "8031",
    "salon": "7230", "spa": "7230", "beauty": "7230", "barber": "7230",
    "nail": "7230", "massage": "7298", "wellness": "7298",
    "laundry": "7216", "dry_clean": "7216", "cleaning": "7349",
    "repair": "7538", "maintenance": "7349", "service": "7699",
    
    # Transportation patterns - comprehensive Foursquare transportation categories
    "airport": "4511", "train": "4112", "bus": "4131", "taxi": "4121",
    "uber": "4121", "lyft": "4121", "rideshare": "4121", "transportation": "4111",
    "parking": "7523", "garage": "7523", "ferry": "4111", "subway": "4111",
    "car_rental": "7512", "truck_rental": "7513", "moving": "4214",
    
    # Entertainment patterns - comprehensive Foursquare entertainment categories
    "cinema": "7832", "movie": "7832", "theater": "7832", "theatre": "7832",
    "park": "7996", "entertainment": "7996", "amusement": "7996", "theme_park": "7996",
    "arcade": "7994", "gaming": "7995", "casino": "7995", "gambling": "7995",
    "museum": "7991", "gallery": "5971", "art": "5971", "exhibition": "7991",
    "zoo": "7998", "aquarium": "7998", "planetarium": "7998",
    "gym": "7997", "fitness": "7997", "workout": "7997", "yoga": "7997",
    "pool": "7997", "swimming": "7997", "tennis": "7997", "golf": "7997",
    "bowling": "7933", "billiard": "7932", "pool_hall": "7932",
    "concert": "7922", "venue": "7922", "event": "7922", "stadium": "7922",
    "nightclub": "5921", "dance": "7922", "karaoke": "7922",
    
    # Professional Services patterns - comprehensive Foursquare professional categories
    "lawyer": "8111", "attorney": "8111", "legal": "8111", "law": "8111",
    "accountant": "8931", "accounting": "8931", "tax": "8931", "bookkeeping": "8931",
    "consulting": "7392", "consultant": "7392", "business": "7392",
    "advertising": "7311", "marketing": "7311", "agency": "7311", "design": "7311",
    "architect": "8911", "architecture": "8911", "engineering": "8911",
    "construction": "1520", "contractor": "1520", "builder": "1520",
    "electrician": "1731", "plumber": "1711", "hvac": "1711", "heating": "1711",
    "painting": "1721", "painter": "1721", "roofing": "1761", "carpenter": "1750",
    "landscaping": "0780", "lawn_care": "0780", "gardening": "0780",
    
    # Education patterns - comprehensive Foursquare education categories
    "school": "8220", "university": "8220", "college": "8220", "education": "8220",
    "elementary": "8211", "primary": "8211", "kindergarten": "8211",
    "daycare": "8351", "childcare": "8351", "preschool": "8351",
    "library": "8231", "study": "8231", "research": "8231",
    "driving_school": "8299", "music_lesson": "8299", "tutoring": "8299",
    
    # Government & Public Services patterns
    "government": "9399", "city_hall": "9399", "courthouse": "9211", "court": "9211",
    "police": "9399", "fire": "9399", "post_office": "9402", "postal": "9402",
    "dmv": "9399", "public": "9399", "municipal": "9399",
    
    # Religious patterns - comprehensive Foursquare religious categories
    "church": "8661", "chapel": "8661", "cathedral": "8661", "mosque": "8661",
    "synagogue": "8661", "temple": "8661", "religious": "8661", "worship": "8661",
    "monastery": "8661", "shrine": "8661", "spiritual": "8661",
    
    # Utilities & Communication patterns
    "utility": "4900", "electric": "4900", "power": "4900", "water": "4900",
    "telephone": "4814", "telecom": "4814", "internet": "4899", "cable": "4899",
    "broadcast": "4899", "communication": "4814",
    
    # Agriculture & Farming patterns
    "farm": "0763", "agriculture": "0763", "farming": "0763", "ranch": "0763",
    "livestock": "0763", "dairy": "0763", "orchard": "0763", "vineyard": "0763",
    
    # Manufacturing & Industrial patterns
    "factory": "5169", "manufacturing": "5169", "industrial": "5169",
    "warehouse": "5169", "distribution": "5169", "logistics": "4214",
    "wholesale": "5169", "supplier": "5169", "chemical": "5169"
}

def get_mcc_for_category(category: str) -> str:
    """
    Get MCC code for a given category
    
    Args:
        category: The business category string
        
    Returns:
        str: The corresponding MCC code or '5999' as fallback
    """
    if not category:
        return "5999"
    
    category_lower = category.lower()
    
    # Check exact matches first
    if category_lower in MCC_CATEGORIES:
        return MCC_CATEGORIES[category_lower]
    
    # Check substring matches
    for pattern, mcc in MCC_CATEGORIES.items():
        if pattern in category_lower or category_lower in pattern:
            return mcc
    
    # Fallback to miscellaneous retail
    return "5999"

def get_mcc_for_google_place_type(place_type: str) -> str:
    """
    Get MCC code for Google Places type using comprehensive mapping
    
    Args:
        place_type: The Google Places type
        
    Returns:
        str: The corresponding MCC code or '5999' as fallback
    """
    if not place_type:
        return "5999"
    
    place_type_lower = place_type.lower()
    
    # Check direct mapping first
    if place_type_lower in GOOGLE_PLACES_TO_MCC:
        return GOOGLE_PLACES_TO_MCC[place_type_lower]
    
    # Check for substring matches in Google Places mapping
    for gp_type, mcc in GOOGLE_PLACES_TO_MCC.items():
        if gp_type in place_type_lower or place_type_lower in gp_type:
            return mcc
    
    # Fall back to general category matching
    return get_mcc_for_category(place_type)

def get_mcc_for_foursquare_category(category_name: str) -> str:
    """
    Get MCC code for Foursquare category using comprehensive mapping
    
    Args:
        category_name: The Foursquare category name
        
    Returns:
        str: The corresponding MCC code or '5999' as fallback
    """
    if not category_name:
        return "5999"
    
    category_lower = category_name.lower()
    
    # Check Foursquare patterns first
    for pattern, mcc in FOURSQUARE_CATEGORY_PATTERNS.items():
        if pattern in category_lower or category_lower in pattern:
            return mcc
    
    # Fall back to general category matching
    return get_mcc_for_category(category_name)

def get_all_mcc_categories():
    """
    Get all available MCC categories
    
    Returns:
        dict: Complete MCC categories mapping
    """
    return MCC_CATEGORIES.copy()

def search_mcc_categories(search_term: str, limit: int = 10):
    """
    Search for MCC categories by term
    
    Args:
        search_term: The term to search for
        limit: Maximum number of results to return
        
    Returns:
        list: List of matching categories with their MCC codes
    """
    if not search_term:
        return []
    
    search_lower = search_term.lower()
    matches = []
    
    for category, mcc in MCC_CATEGORIES.items():
        if search_lower in category or category in search_lower:
            matches.append({
                "category": category,
                "mcc": mcc
            })
        
        if len(matches) >= limit:
            break
    
    return matches 