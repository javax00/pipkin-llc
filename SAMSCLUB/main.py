import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import concurrent.futures
import math
from datetime import datetime
import urllib.parse
import re

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_samsclub_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Source Link']
############################# CSV WRITE #################################
script_dir = os.path.dirname(os.path.abspath(__file__))					#
write_csv = os.path.join(script_dir, write_filename)					#
if os.path.exists(write_csv):											#
	os.remove(write_csv)												#
	print(f"Deleted existing file: {write_csv}\nStarting now...\n")		#
																		#
with open(write_csv, 'w', newline='', encoding='utf-8') as f:			#
	writer = csv.writer(f)												#
	writer.writerow(write_headers)										#
############################# CSV WRITE #################################

urls = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
	}
	# r = requests.get(zenrows_api, params=params, timeout=90)
	r = requests.get(target_url, timeout=90)
	return r.text

def convert_11_12(upc11):
	digits = [int(x) for x in str(upc11)]
	if len(digits) != 11:
		raise ValueError("Input must be 11 digits")
	odd_sum = sum(digits[::2])
	even_sum = sum(digits[1::2])
	total = (odd_sum * 3) + even_sum
	check_digit = (10 - (total % 10)) % 10
	return f"{upc11}{check_digit}"

def get_product_links(page):
	url = f"https://www.samsclub.com/orchestra/home/graphql/browse?page={page}&prg=desktop&catId=1429&sort=relevance&ps=45&limit=45&additionalQueryParams.isMoreOptionsTileEnabled=true&additionalQueryParams.isGenAiEnabled=undefined&additionalQueryParams.view_module=undefined&additionalQueryParams.search_ctx=undefined&additionalQueryParams.neuralSearchSeeAll=false&additionalQueryParams.isModuleArrayReq=undefined&searchArgs.cat_id=1429&searchArgs.prg=desktop&ffAwareSearchOptOut=false&enableDesktopHighlights=undefined&enableVolumePricing=undefined&fitmentFieldParams=true_true_true_false&searchParams.page={page}&searchParams.prg=desktop&searchParams.catId=1429&searchParams.sort=relevance&searchParams.ps=45&searchParams.limit=45&searchParams.additionalQueryParams.isMoreOptionsTileEnabled=true&searchParams.additionalQueryParams.isGenAiEnabled=undefined&searchParams.additionalQueryParams.view_module=undefined&searchParams.additionalQueryParams.search_ctx=undefined&searchParams.additionalQueryParams.neuralSearchSeeAll=false&searchParams.additionalQueryParams.isModuleArrayReq=undefined&searchParams.searchArgs.cat_id=1429&searchParams.searchArgs.prg=desktop&searchParams.ffAwareSearchOptOut=false&searchParams.enableDesktopHighlights=undefined&searchParams.enableVolumePricing=undefined&searchParams.cat_id=1429&enableFashionTopNav=false&fetchMarquee=true&fetchSkyline=true&fetchSbaTop=true&fetchSBAV1=false&fetchGallery=false&fetchDac=true&enablePortableFacets=true&tenant=SAMS_GLASS&pageType=BrowsePage&enableFacetCount=true&marketSpecificParams=undefined&enableMultiSave=false&enableInStoreShelfMessage=false&fSeo=true&enableSellerType=false&enableItemRank=false&enableFulfillmentTagsEnhacements=false&enableRxDrugScheduleModal=false&enablePromoData=false&enableAdsPromoData=false&enableSeoLangUrl=false&enableImageBannerCarousel=true&enableHero4=false&enablePromotionMessages=true&enableSignInToSeePrice=true&enableSimpleEmailSignUp=false&enableModuleReposition=true"

	payload = json.dumps({
	"query": "query Browse( $query:String $limit:Int $page:Int $prg:Prg! $facet:String $sort:Sort $catId:String! $max_price:String $min_price:String $module_search:String $affinityOverride:AffinityOverride $pap:String $ps:Int $ptss:String $beShelfId:String $fitmentFieldParams:JSON ={}$fitmentSearchParams:JSON ={}$searchParams:JSON ={}$rawFacet:String $seoPath:String $trsp:String $fetchMarquee:Boolean! $fetchSkyline:Boolean! $fetchGallery:Boolean! $fetchSbaTop:Boolean! $fetchSBAV1:Boolean! $enableAdsPromoData:Boolean = false $fetchDac:Boolean! $additionalQueryParams:JSON ={}$enablePortableFacets:Boolean = false $enableFashionTopNav:Boolean = false $intentSource:IntentSource $tenant:String! $enableFacetCount:Boolean = true $pageType:String! = \"BrowsePage\" $marketSpecificParams:String $enableMultiSave:Boolean = false $fSeo:Boolean = true $enableSellerType:Boolean = false $enableItemRank:Boolean = false $enableAdditionalSearchDepartmentAnalytics:Boolean = false $enableFulfillmentTagsEnhacements:Boolean = false $disableAds:Boolean = false $enableRxDrugScheduleModal:Boolean = false $enablePromoData:Boolean = false $fetchBadSplit:Boolean = false $enableSeoLangUrl:Boolean = false $enableSignInToSeePrice:Boolean = false $enableImageBannerCarousel:Boolean = false $enableHero4:Boolean = false $enableInStoreShelfMessage:Boolean = false $enableShopSimilarBottomSheet:Boolean = false $enablePromotionMessages:Boolean = false $enableItemLimits:Boolean = false $enableCanAddToList:Boolean = false $enableIsFreeWarranty:Boolean = false $enableSimpleEmailSignUp:Boolean = false $enableDesktopHighlights:Boolean = false $enableVolumePricing:Boolean = false ){search( query:$query limit:$limit page:$page prg:$prg pap:$pap facet:$facet sort:$sort cat_id:$catId max_price:$max_price min_price:$min_price module_search:$module_search affinityOverride:$affinityOverride additionalQueryParams:$additionalQueryParams ps:$ps ptss:$ptss trsp:$trsp intentSource:$intentSource _be_shelf_id:$beShelfId pageType:$pageType ){query searchResult{...BrowseResultFragment}}contentLayout( channel:\"WWW\" pageType:$pageType tenant:$tenant version:\"v1\" searchArgs:{query:$query cat_id:$catId _be_shelf_id:$beShelfId prg:$prg}){modules( p13n:{page:$page userReqInfo:{refererContext:{catId:$catId}}}){...ModuleFragment configs{__typename...on EnricherModuleConfigsV1{zoneV1}...on TempoWM_GLASSWWWEmailSignUpWidgetConfigs{_rawConfigs}...GenericSortAndFilterModule...on TempoWM_GLASSWWWPillsModuleConfigs{moduleSource pillsV2{...GenericPillsModuleFragment}}...TileTakeOverProductFragment...TileDisplayAdFragment...on TempoWM_GLASSWWWSearchFitmentModuleConfigs{fitments( fitmentSearchParams:$fitmentSearchParams fitmentFieldParams:$fitmentFieldParams ){...FitmentFragment sisFitmentResponse{...BrowseResultFragment}}}...on TempoWM_GLASSWWWSearchACCStoreSelectionConfigs{ctaText userInfoMessage headingDetails{heading headingWhenFulfillmentIsSelectedAsPickup}}...on TempoWM_GLASSWWWStoreSelectionHeaderConfigs{fulfillmentMethodLabel storeDislayName}...on TempoWM_GLASSWWWSponsoredProductCarouselConfigs{_rawConfigs}...on _TempoWM_GLASSWWWSearchHeaderModuleConfigs{_rawConfigs}...on TempoWM_GLASSWWWBenefitProgramBannerPlaceholderConfigs{_rawConfigs}...on TempoWM_GLASSWWWBrowseRelatedShelves @include(if:$fSeo){seoBrowseRelmData( id:$catId marketSpecificParams:$marketSpecificParams ){relm{id url name}}}...TopNavFragment @include(if:$enableFashionTopNav)...BrandAmplifierAdConfigs @include(if:$fetchSbaTop)...PopularInModuleFragment...CopyBlockModuleFragment...BannerModuleFragment...Hero4Fragment @include(if:$enableHero4)...HeroPOVModuleFragment...InlineSearchModuleFragment...MarqueeDisplayAdConfigsFragment @include(if:$fetchMarquee)...SkylineDisplayAdConfigsFragment @include(if:$fetchSkyline)...GalleryDisplayAdConfigsFragment @include(if:$fetchGallery)...DynamicAdContainerConfigsFragment @include(if:$fetchDac)...HorizontalChipModuleConfigsFragment...SkinnyBannerFragment...GenericSeoFaqFragment...SponsoredVideoAdFragment...AlertBannerListFragment...ImageBannerCarouselFragment @include(if:$enableImageBannerCarousel)...SimpleEmailSignUpFragment @include(if:$enableSimpleEmailSignUp)...MosaicGridFragment...FaqFragment}}...LayoutFragment pageMetadata{location{pickupStore deliveryStore intent postalCode stateOrProvinceCode city storeId accessPointId accessType spokeNodeId}pageContext}}seoBrowseMetaData( id:$catId facets:$rawFacet path:$seoPath facet_query_param:$facet _be_shelf_id:$beShelfId marketSpecificParams:$marketSpecificParams page:$page ){metaTitle metaDesc metaCanon h1 noIndex languageUrls{name url}}}fragment BrowseResultFragment on SearchInterface{title aggregatedCount...GenericBreadCrumbFragment...ShelfDataFragment...GenericDebugFragment...GenericItemStacksFragment...GenericPageMetaDataFragment...GenericPaginationFragment...GenericRequestContextFragment...GenericErrorResponse modules{facetsV1 @skip(if:$enablePortableFacets){...GenericFacetFragment}topNavFacets @include(if:$enablePortableFacets){...GenericFacetFragment}allSortAndFilterFacets @include(if:$enablePortableFacets){...GenericFacetFragment}pills{...GenericPillsModuleFragment}bannerMessages{message type linkText linkUrl}}pac{relevantPT{productType score}showPAC reasonCode}}fragment ModuleFragment on TempoModule{__typename type name version moduleId schedule{priority}matchedTrigger{zone}}fragment LayoutFragment on ContentLayout{layouts{id layout}}fragment GenericBreadCrumbFragment on SearchInterface{breadCrumb{id name url cat_level}}fragment ShelfDataFragment on SearchInterface{shelfData{shelfName shelfId}}fragment GenericDebugFragment on SearchInterface{debug{statusCode responseTimeMillis scsTimeMillis sisUrl adsUrl genAIDebugInfo{searchAlgorithm isGenAiQueryEligible genAIUnavailableReason reformulatedQuery}presoDebugInformation{explainerToolsResponse}}}fragment GenericItemStacksFragment on SearchInterface{itemStacks{displayMessage meta{beacon suppressTitle isSponsored adsBeacon{adUuid moduleInfo max_ads adSlots}spBeaconInfo{adUuid moduleInfo pageViewUUID placement max}query isPartialResult stackId stackType stackName title description subTitle titleKey subType queryUsedForSearchResults layoutEnum totalItemCount totalItemCountDisplay viewAllParams{query cat_id sort facet affinityOverride recall_set groupIdentifier min_price max_price view_module shouldHide buttonTitle}comparisonCart{product_type}borderColor iconUrl initialCount fulfillmentIntent}itemsV2{...GenericItemFragment...GenericInGridMarqueeAdFragment @skip(if:$disableAds)...GenericInGridAdFragment @skip(if:$disableAds)...GenericTileTakeOverTileFragment...InlineCategoryNavigationFragment}content{title subtitle data{type name displayName url urlParams imageUrl}}}}fragment GenericItemFragment on Product{__typename buyBoxSuppression similarItems id usItemId specialCtaType @include(if:$enableSignInToSeePrice) isBadSplit @include(if:$fetchBadSplit) catalogSellerId rxDrugScheduleType @include(if:$enableRxDrugScheduleModal) wfsEnabled @include(if:$enableSellerType) itemRank @include(if:$enableItemRank) fitmentLabel name checkStoreAvailabilityATC seeShippingEligibility brand type shortDescription weightIncrement topResult additionalOfferCount availabilityInNearbyStore itemBeacon catalogProductType conditionPriceRange{otherConditionsMessage minPriceDisplay}imageInfo{...GenericProductImageInfoFragment}aspectInfo{name header id snippet}plItem{isPLItemToBoost plItemTagString}canonicalUrl conditionV2{code groupCode}externalInfo{url}itemType productAttributes @include(if:$enableDesktopHighlights){productHighlights{name value}}promotionMessages @include(if:$enablePromotionMessages){type badgeBackgroundColor badgeStyleId badgeTextColor badgeTitle bundledDisplayName expiryDateMessage limitMessage message popupMessage specialMessage}category{categoryPathId path{name url}}returnPolicy{returnable freeReturns returnWindow{value unitType}returnPolicyText}discounts{...GenericProductDiscountsFragment}conditionV2{code groupCode}badges{flags{__typename...on BaseBadge{key bundleId @include(if:$enableMultiSave) text type id styleId}...on PreviouslyPurchasedBadge{id text key lastBoughtOn numBought}}tags{__typename...on BaseBadge{key text type}}groups{__typename name members{...on BadgeGroupMember{__typename id key memberType otherInfo{moqText}rank textTemplate textValues slaText slaDate slaDateISO sla{regular faster unscheduled}styleId text type iconId templates{regular faster unavailable}badgeContent{type value styleId id canonicalUrl athAsset athModule}}...on CompositeGroupMember{__typename join memberType styleId suffix members{__typename id key memberType rank slaText styleId text type iconId}}}}...GenericBadgeFragment}buyNowEligible classType averageRating numberOfReviews esrb mediaRating salesUnitType sellerId sellerName sellerType hasSellerBadge isEarlyAccessItem preEarlyAccessEvent earlyAccessEvent blitzItem annualEvent annualEventV2 availabilityStatusV2{display value}availabilityMessage @include(if:$enableInStoreShelfMessage) groupMetaData{groupType groupSubType numberOfComponents groupComponents{quantity offerId componentType productDisplayName}}addOnServices{...AddOnServicesFragment}productLocation{displayValue aisle{zone aisle}}fulfillmentSpeed offerId offerType @include(if:$enableFulfillmentTagsEnhacements) preOrder{...GenericPreorderFragment}pac{showPAC reasonCode fulfillmentPacModule}fulfillmentSummary{fulfillment storeId deliveryDate fulfillmentMethods fulfillmentBadge outOfCountryEligible}priceInfo{...GenericProductPriceInfoFragment}variantCriteria{...GenericVariantCriteriaFragment}snapEligible fulfillmentTitle fulfillmentType brand manufacturerName showAtc sponsoredProduct{spQs clickBeacon spTags viewBeacon}showOptions showBuyNow quickShop quickShopCTALabel rewards{eligible state minQuantity rewardAmt promotionId selectionToken rewardMultiplierStr cbOffer term expiry description}promoData @include(if:$enablePromoData){type terms templateData{priceString imageUrl}}promoDiscount{discount discountEligible discountEligibleVariantPresent promotionId promoOffer state showOtherEligibleItemsCTA type min awardValue awardSubType tiers{awardValue minQuantity}}arExperiences{isARHome isZeekit isAROptical}eventAttributes{...GenericProductEventAttributesFragment}subscription{subscriptionEligible subscriptionTransactable}hasCarePlans petRx{eligible singleDispense}vision{ageGroup visionCenterApproved}showExploreOtherConditionsCTA isPreowned pglsCondition newConditionProductId preownedCondition keyAttributes{displayEnum value}mhmdFlag seeSimilar subscription{subscriptionEligible subscriptionTransactable showSubscriptionCTA}isSimilarLookEligible @include(if:$enableShopSimilarBottomSheet) winningProductId @include(if:$enableShopSimilarBottomSheet) orderLimit @include(if:$enableItemLimits) orderMinLimit @include(if:$enableItemLimits) canAddToList @include(if:$enableCanAddToList) isFreeWarranty @include(if:$enableIsFreeWarranty)}fragment GenericProductPriceInfoFragment on ProductPriceInfo{priceRange{minPrice maxPrice priceString}subscriptionDiscountPrice{priceString}currentPrice{...GenericProductPriceFragment priceDisplay}comparisonPrice{...GenericProductPriceFragment}wasPrice{...GenericProductPriceFragment}unitPrice{...GenericProductPriceFragment}listPrice{...GenericProductPriceFragment}savingsAmount{...GenericProductSavingsFragment}shipPrice{...GenericProductPriceFragment}additionalFees{dutyFee{price}}subscriptionPrice{priceString subscriptionString downPaymentString}priceDisplayCodes{priceDisplayCondition finalCostByWeight submapType isB2BPrice priceDisplayType}wPlusEarlyAccessPrice{memberPrice{...GenericProductPriceFragment}savings{...GenericProductSavingsFragment}eventStartTime eventStartTimeDisplay}subscriptionDualPrice subscriptionPercentage volumePriceTiers @include(if:$enableVolumePricing){currencyUnit minUnit price savingsAmount}}fragment GenericProductSavingsFragment on ProductSavings{amount percent priceString}fragment GenericProductPriceFragment on ProductPrice{price priceString variantPriceString priceType currencyUnit priceDisplay}fragment GenericProductEventAttributesFragment on EventAttributes{priceFlip specialBuy}fragment GenericPreorderFragment on PreOrder{isPreOrder preOrderMessage preOrderStreetDateMessage streetDate streetDateDisplayable streetDateType releaseDate}fragment GenericVariantCriteriaFragment on VariantCriterion{name type id displayName isVariantTypeSwatch isVariantTypeAllowed variantList{id images name rank displayName swatchImageUrl availabilityStatus products selectedProduct{canonicalUrl usItemId}}}fragment GenericProductDiscountsFragment on Discounts{discountedValue{price priceString}discountMetaData{id type savings{amount priceString percent}price{price priceString priceDisplay}unitPrice{price priceString}comparisonPrice{price priceString}unitPriceDisplayCondition}}fragment GenericProductImageInfoFragment on ProductImageInfo{id name thumbnailUrl size allImages{id url type}}fragment GenericBadgeFragment on UnifiedBadge{groupsV2{name flow pos members{memType memId memStyleId fbMemStyleId content{type value styleId fbStyleId contDesc url actionId}}}}fragment AddOnServicesFragment on AddOnService{serviceType serviceTitle serviceSubTitle serviceProviders groups{groupType groupTitle assetUrl shortDescription unavailabilityReason nearByStores{nodes{id displayName distance}}services{offerId}}}fragment GenericInGridMarqueeAdFragment on MarqueePlaceholder{__typename type moduleLocation lazy}fragment GenericInGridAdFragment on AdPlaceholder{__typename type moduleLocation lazy adUuid hasVideo moduleInfo videoAdType}fragment GenericTileTakeOverTileFragment on TileTakeOverProductPlaceholder{__typename type tileTakeOverTile{span title subtitle image{src alt assetId assetName}logoImage{src alt}backgroundColor titleTextColor subtitleTextColor tileCta{ctaLink{clickThrough{value}linkText title}ctaType ctaTextColor}adsEnabled adCardLocation enableLazyLoad}}fragment InlineCategoryNavigationFragment on InlineCategoryNavigationPlaceholder{__typename type}fragment GenericPageMetaDataFragment on SearchInterface{pageMetadata{categoryNavigationMetaData{experienceType}storeSelectionHeader{fulfillmentMethodLabel storeDislayName}title canonical source description location{addressId}subscriptionEligible languageUrls @include(if:$enableSeoLangUrl){name url}noIndex}}fragment GenericPaginationFragment on SearchInterface{paginationV2{maxPage pageProperties}}fragment GenericRequestContextFragment on SearchInterface{requestContext{vertical hasGicIntent isFitmentFilterQueryApplied searchMatchType selectedFacetCount showComparisonCart categories{id name}}}fragment GenericErrorResponse on SearchInterface{errorResponse{correlationId source errorCodes errors{errorType statusCode statusMsg source}}}fragment GenericPillsModuleFragment on PillsSearchInterface{title titleColor url image:imageV1{src alt assetId assetName}}fragment BannerViewConfigFragment on BannerViewConfigCLS{title image imageAlt displayName description url urlAlt appStoreLink appStoreLinkAlt playStoreLink playStoreLinkAlt}fragment BannerModuleFragment on TempoWM_GLASSWWWSearchBannerConfigs{moduleType viewConfig{...BannerViewConfigFragment}}fragment PopularInModuleFragment on TempoWM_GLASSWWWPopularInBrowseConfigs{seoBrowseRelmData(id:$catId){relm{id name url}}}fragment CopyBlockModuleFragment on TempoWM_GLASSWWWCopyBlockConfigs{copyBlock( facets:$rawFacet id:$catId marketSpecificParams:$marketSpecificParams ){cwc}}fragment GenericFacetFragment on Facet{title name expandOnLoad type displayType urlParams url layout min max selectedMin selectedMax unboundedMax stepSize isSelected valueDisplayLimit values{id title name expandOnLoad description type itemCount @include(if:$enableFacetCount) url isSelected baseSeoURL catPathName @include(if:$enableAdditionalSearchDepartmentAnalytics) values{id title name expandOnLoad description type itemCount @include(if:$enableFacetCount) url isSelected baseSeoURL values{id title name expandOnLoad description type itemCount @include(if:$enableFacetCount) isSelected baseSeoURL values{id title name expandOnLoad description type itemCount @include(if:$enableFacetCount) isSelected baseSeoURL values{id title name expandOnLoad description type itemCount @include(if:$enableFacetCount) isSelected baseSeoURL values{id title name expandOnLoad description type itemCount @include(if:$enableFacetCount) isSelected baseSeoURL values{id title name expandOnLoad description type itemCount @include(if:$enableFacetCount) isSelected baseSeoURL values{id title name expandOnLoad description type itemCount @include(if:$enableFacetCount) isSelected baseSeoURL}}}}}}}}}fragment FitmentFragment on Fitments{partTypeIDs fitmentType isNarrowSearch fitmentOptionalFields{...FitmentFieldFragment}result{fitmentType status formId position quantityTitle spec{...FitmentSpecFragment}extendedAttributes{...FitmentFieldFragment}labels{...LabelFragment}resultSubTitle notes suggestions{...FitmentSuggestionFragment}oilChangeSchedulingInfo{formattedOilViscosity oilViscosity oilViscosityLabel formattedOilType oilType oilTypeLabel formattedOilCapacity oilCapacityQuarts oilCapacityLabel fittingOilFilters{brand manufacturerNumber}}}redirectUrl{title clickThrough{value}}labels{...LabelFragment}savedVehicle{vehicleType{...VehicleFieldFragment}vehicleYear{...VehicleFieldFragment}vehicleMake{...VehicleFieldFragment}vehicleModel{...VehicleFieldFragment}additionalAttributes{...VehicleFieldFragment}}fitmentFields{...VehicleFieldFragment}fitmentForms{id fields{...FitmentFieldFragment}title labels{...LabelFragment}garage{vehicles{...AutoVehicle}}}}fragment LabelFragment on FitmentLabels{ctas{...FitmentLabelEntityFragment}messages{...FitmentLabelEntityFragment}links{...FitmentLabelEntityFragment}images{...FitmentLabelEntityFragment}}fragment FitmentLabelEntityFragment on FitmentLabelEntity{id label}fragment VehicleFieldFragment on FitmentVehicleField{id label value}fragment FitmentSpecFragment on FitmentSpecValue{label displayValue}fragment FitmentFieldFragment on FitmentField{id displayName value extended data{value label}dependsOn isRequired errorMessage}fragment FitmentSuggestionFragment on FitmentSuggestion{id position loadIndex speedRating searchQueryParam labels{...LabelFragment}cat_id fitmentSuggestionParams{id value}optionalSuggestionParams{id value displayName data{label value}dependsOn isRequired errorMessage}applicationSuggestionParams{position}}fragment Hero4Fragment on TempoWM_GLASSWWWHero4Configs{hero4DesktopImage:desktopImage{src}hero4MobileImage:mobileImage{alt src}hero4VerticalImagePosition:verticalImagePosition hero4HorizontalImagePosition:horizontalImagePosition hero4Eyebrow:eyebrow hero4Heading:heading{text textColor}subheading emphasizedText{text textColor}hero4CTA:primaryCTA{clickThrough{value}linkText}hero4AlertBanner:alertBanner{alertType title bodyCopy actionCta{uid title linkText clickThrough{value}}}bulletedList{bulletedIcon{alt src}bulletedText}additionalAssistance{text tertiaryCtaText tertiaryCtaType externalLink modalHeading modalBody}disclaimerText disclaimerCta{tertiaryCtaText tertiaryCtaType externalLink modalHeading modalBody}}fragment HeroPOVModuleFragment on TempoWM_GLASSWWWHeroPovConfigsV1{povCards{card:cardV1{povStyle image{mobileImage{...TempoCommonImageFragment}desktopImage{...TempoCommonImageFragment}}heading{text textColor textSize}subheading{text textColor}detailsView{backgroundColor isTransparent alignment}ctaButton{button{linkText clickThrough{value}uid}ctaButtonBackgroundColor textColor}legalDisclosure{regularText shortenedText textColor textColorMobile legalBottomSheetTitle legalBottomSheetDescription}logo{...TempoCommonImageFragment}links{link{...TempoCommonLinkFragment}textColor textColorMobile}}}}fragment TempoCommonImageFragment on TempoCommonImage{src alt assetId uid clickThrough{value}}fragment TempoCommonLinkFragment on TempoCommonStringLink{linkText title uid clickThrough{value}}fragment InlineSearchModuleFragment on TempoWM_GLASSWWWInlineSearchConfigs{headingText placeholderText headingTextColor}fragment MarqueeDisplayAdConfigsFragment on TempoWM_GLASSWWWMarqueeDisplayAdConfigs{_rawConfigs ad{...DisplayAdFragment}}fragment DisplayAdFragment on Ad{...AdFragment adContent{type data{__typename...AdDataDisplayAdFragment...AdDataDisplayAdDSPFragment}}}fragment AdFragment on Ad{status moduleType platform pageId pageType storeId stateCode zipCode pageContext moduleConfigs adsContext adRequestComposite}fragment AdDataDisplayAdFragment on AdData{...on DisplayAd{json status}}fragment AdDataDisplayAdDSPFragment on AdData{...on MultiImpDspAd{ads{assets eventTrackers link metaData templateId variantId availableVariantIds}}...on DisplayAdDSP{assets eventTrackers link metaData templateId variantId availableVariantIds}}fragment SkylineDisplayAdConfigsFragment on TempoWM_GLASSWWWSkylineDisplayAdConfigs{_rawConfigs ad{...SkylineDisplayAdFragment}}fragment SkylineDisplayAdFragment on Ad{...SkylineAdFragment adContent{type data{__typename...SkylineAdDataDisplayAdFragment...SkylineAdDataDisplayAdDSPFragment}}}fragment SkylineAdFragment on Ad{status moduleType platform pageId pageType storeId stateCode zipCode pageContext moduleConfigs adsContext adRequestComposite}fragment SkylineAdDataDisplayAdFragment on AdData{...on DisplayAd{json status}}fragment SkylineAdDataDisplayAdDSPFragment on AdData{...on MultiImpDspAd{ads{assets eventTrackers link metaData templateId variantId availableVariantIds}}...on DisplayAdDSP{assets eventTrackers link metaData templateId variantId availableVariantIds}}fragment GalleryDisplayAdConfigsFragment on TempoWM_GLASSWWWGalleryDisplayAdConfigs{_rawConfigs}fragment DynamicAdContainerConfigsFragment on TempoWM_GLASSWWWDynamicAdContainerConfigs{_rawConfigs adModules{moduleType moduleLocation priority}zoneLocation lazy}fragment MosaicGridFragment on TempoWM_GLASSWWWMosaicGridConfigs{paginationEnabled backgroundColor dWebGridStartingDirection backgroundImage{src alt assetId assetName}tabList{tabName shelfId initialDisplaySize}pillList{pillName pillUrl{title clickThrough{value}}}expandCollapseDetails{collapsedStateItemCount collapsedStateButtonTitle expandedStateButtonTitle}mosaicPageType bannerList{backgroundColor titleDetails{title titleColor fontType}subTitleDetails{subTitle subTitleColor fontType}ctaDetails{ctaTitle ctaTextColor ctaLink ctaType}mwebBackgroundImage{src alt assetId assetName}dwebBackgroundImage{src alt assetId assetName}}placeholderTile{backgroundColor titleDetails{title titleColor fontType}ctaDetails{ctaTitle ctaTextColor ctaLink ctaType}span1BackgroundImage{src alt}span2BackgroundImage{src alt}}footerDetails{backgroundColor titleDetails{title titleColor fontType}subTitleDetails{subTitle subTitleColor fontType}ctaDetails{ctaTitle ctaTextColor ctaLink ctaType}mwebBackgroundImage{src alt}dwebBackgroundImage{src alt}}headerDetails{titleDetails{title titleColor fontType titleAlignment}subTitleDetails{subTitle subTitleColor fontType titleAlignment}}tileTakeOverList{...TileTakeOverListFragment}mixedResults{__typename...on TempoWM_GLASSWWWMosaicGridConfigsTileTakeOverList{...TileTakeOverListFragment}...on TempoWM_GLASSWWWMosaicGridConfigsBannerList{...BannerListFragment}}dealsMosaic(searchParams:$searchParams){...GenericItemStacksFragment...GenericPaginationFragment...GenericErrorResponse}}fragment TileTakeOverListFragment on TempoWM_GLASSWWWMosaicGridConfigsTileTakeOverList{__typename backgroundColor mWebBackgroundImage{src}dWebBackgroundImage{src}tileTakeOverGroupPosition headlineDetails{headline headlineColor fontType}subheadDetails{subhead subHeadColor fontType}tileCta{ctaStyle ctaType ctaTypeMoreInfo{moreInfoTitle moreInfoDescription moreInfoLink{linkText title clickThrough{value rawValue}}}ctaLink{linkText title clickThrough{value rawValue}}ctaTextColor ctaPosition}}fragment BannerListFragment on TempoWM_GLASSWWWMosaicGridConfigsBannerList{__typename backgroundColor mwebBackgroundImage{alt src}dwebBackgroundImage{alt src}titleDetails{title titleColor fontType}subTitleDetails{subTitle subTitleColor fontType}ctaDetails{ctaTitle ctaLink ctaTextColor ctaType}}fragment HorizontalChipModuleConfigsFragment on TempoWM_GLASSWWWHorizontalChipModuleConfigs{chipModuleSource:moduleSource heading headingColor backgroundImage{src alt}backgroundColor desktopImageHeight desktopImageWidth mobileImageHeight mobileImageWidth chipModule{title url{linkText title clickThrough{type value}}}chipModuleWithImages{title titleColor url{linkText title clickThrough{type value}}image{assetId assetName alt clickThrough{type value}height src title width}}}fragment SkinnyBannerFragment on TempoWM_GLASSWWWSkinnyBannerConfigs{campaignsV1{bannerType desktopBannerHeight bannerImage{src title alt assetId assetName}mobileBannerHeight mobileImage{src title alt assetId assetName}clickThroughUrl{clickThrough{value}}backgroundColor heading{title fontColor}subHeading{title fontColor}bannerCta{ctaLink{linkText clickThrough{value}}textColor ctaType}}}fragment TileTakeOverProductFragment on TempoWM_GLASSWWWTileTakeOverProductConfigs{dwebSlots mwebSlots overrideDefaultTiles TileTakeOverProductDetailsV1{pageNumber span dwebPosition mwebPosition title subtitle image{src alt assetId assetName}logoImage{src alt}backgroundColor titleTextColor subtitleTextColor tileCta{ctaLink{clickThrough{value}linkText title uid}ctaType ctaTextColor}adsEnabled adCardLocation enableLazyLoad}}fragment TileDisplayAdFragment on TempoWM_GLASSWWWTileDisplayAdConfigs{_rawConfigs dwebSlots mwebSlots TileDisplayAdCardDetails{...on TempoWM_GLASSWWWTileDisplayAdConfigsTileDisplayAdCardDetails{moduleLocation lazy pageNumber span dwebPosition mwebPosition clientCapabilities ad{adContent{data{...on DisplayAd{json}...on DisplayAdDSP{assets eventTrackers link metaData templateId variantId availableVariantIds}}}adRequestComposite adsContext moduleType pageContext stateCode status storeId zipCode}}}}fragment TopNavFragment on TempoWM_GLASSWWWCategoryTopNavConfigs{navHeaders{header{linkText clickThrough{value}}headerImageGroup{headerImage{alt src assetName assetId}imgTitle imgSubText imgLink{linkText title clickThrough{value}}}categoryGroup{category{linkText clickThrough{value}}startNewColumn subCategoryGroup{subCategory{linkText clickThrough{value}}isBold openInNewTab}}}}fragment AlertBannerListFragment on TempoSAMS_GLASSWWWAlertBannerListConfigs{AlertBannerList{message type actionCta{title clickThrough{type value}}}}fragment BrandAmplifierAdConfigs on TempoWM_GLASSWWWBrandAmplifierAdConfigs{_rawConfigs moduleLocation ad{...SponsoredBrandsAdFragment}}fragment SponsoredBrandsAdFragment on Ad{...AdFragment adContent{type data @skip(if:$fetchSBAV1){__typename...AdDataSponsoredBrandsFragment}dataV1 @include(if:$fetchSBAV1){__typename...AdDataSponsoredBrandsV1Fragment}}}fragment AdDataSponsoredBrandsFragment on AdData{...on SponsoredBrands{adUuid adExpInfo moduleInfo brands{logo{featuredHeadline featuredImage featuredImageName featuredUrl logoClickTrackUrl}products{...ProductFragment}}}}fragment AdDataSponsoredBrandsV1Fragment on AdData{...on SponsoredBrandsV1{adUuid adExpInfo moduleInfo brands{logo{featuredHeadline featuredImage featuredImageName featuredUrl logoClickTrackUrl}products{...ProductFragment}customInfo{images}}}}fragment ProductFragment on Product{usItemId offerId specialCtaType @include(if:$enableSignInToSeePrice) orderMinLimit @include(if:$enableItemLimits) orderLimit @include(if:$enableItemLimits) badges{flags{__typename...on BaseBadge{id text key query type styleId}...on PreviouslyPurchasedBadge{id text key lastBoughtOn numBought criteria{name value}}}labels{__typename...on BaseBadge{id text key}...on PreviouslyPurchasedBadge{id text key lastBoughtOn numBought}}tags{__typename...on BaseBadge{id text key}}groups{__typename name members{...on BadgeGroupMember{__typename id key memberType rank slaText styleId text type}...on CompositeGroupMember{__typename join memberType styleId suffix members{__typename id key memberType rank slaText styleId text type}}}}groupsV2{name flow pos members{memType memId memStyleId fbMemStyleId content{type value styleId fbStyleId contDesc url actionId}}}}priceInfo{priceDisplayCodes{rollback reducedPrice eligibleForAssociateDiscount clearance strikethrough submapType priceDisplayCondition unitOfMeasure pricePerUnitUom}currentPrice{price priceString priceDisplay}wasPrice{price priceString}listPrice{price priceString}priceRange{minPrice maxPrice priceString}unitPrice{price priceString}savingsAmount{amount priceString}comparisonPrice{priceString}subscriptionPrice{priceString subscriptionString price minPrice maxPrice intervalFrequency duration percentageRate durationUOM interestUOM downPaymentString}wPlusEarlyAccessPrice{memberPrice{price priceString priceDisplay}savings{amount priceString}eventStartTime eventStartTimeDisplay}}preOrder{streetDate streetDateDisplayable streetDateType isPreOrder preOrderMessage preOrderStreetDateMessage}annualEventV2 earlyAccessEvent isEarlyAccessItem eventAttributes{priceFlip specialBuy}snapEligible showOptions promoData @include(if:$enableAdsPromoData){type templateData{priceString imageUrl}}sponsoredProduct{spQs clickBeacon spTags}canonicalUrl conditionV2{code groupCode}numberOfReviews averageRating availabilityStatus imageInfo{thumbnailUrl allImages{id url}}name fulfillmentBadge classType type showAtc brand sellerId sellerName sellerType rxDrugScheduleType @include(if:$enableRxDrugScheduleModal)}fragment AutoVehicle on AutoVehicle{cid color default documentType fitment{baseBodyType baseVehicleId driveType{id name}engineOptions{id isSelected label}smartSubModel tireSizeOptions{diameter isCustom isSelected loadIndex positions ratio speedRating tirePressureFront tirePressureRear tireSize width}trim}isDually licensePlate licensePlateState licensePlateStateCode make model reminders{id}source sourceType subModel{subModelId subModelName}subModelOptions{subModelId subModelName}vehicleId vehicleType vin year}fragment GenericSeoFaqFragment on TempoWM_GLASSWWWGenericSEOFAQModuleConfigs{seoFaqList:faqList(id:$catId pageType:$pageType){seoFaqQuestion:questionText seoFaqAnswer:answerParagraphs}}fragment SponsoredVideoAdFragment on TempoWM_GLASSWWWSponsoredVideoAdConfigs{__typename sponsoredVideoAd{ad{adContent{data{...on SponsoredVideos{adUuid hasVideo moduleInfo}}}}}}fragment GenericSortAndFilterModule on _TempoWM_GLASSWWWSearchSortFilterModuleConfigs{facetsV1 @skip(if:$enablePortableFacets){...GenericFacetFragment}topNavFacets{...GenericFacetFragment}allSortAndFilterFacets{...GenericFacetFragment}sortByColor}fragment ImageBannerCarouselFragment on TempoSAMS_GLASSWWWImageBannerCarouselConfigs{autoRotation desktopBannerHeight mobileBannerHeight image{desktopImage{src title alt assetId assetName}mobileImage{src title alt assetId assetName}clickThroughUrl{clickThrough{value}}}}fragment SimpleEmailSignUpFragment on TempoWM_GLASSWWWSimpleEmailSignUpConfigs{simpleEmailContent{contentPosition textAlign fontSize textPartsType{text bold url lineBreak}}simpleEmailBannerImages{imagePosition imageType{src alt width height uid}}simpleEmailBackgroundColor}fragment FaqFragment on TempoWM_GLASSWWWFAQConfigs{title faqList{questionText answerParagraphs{paragraph}}}",
	"variables": {
		"id": "",
		"dealsId": "",
		"query": "",
		"nudgeContext": "",
		"page": page,
		"prg": "desktop",
		"catId": "1429",
		"facet": "",
		"sort": "relevance",
		"rawFacet": "",
		"seoPath": "",
		"ps": 45,
		"limit": 45,
		"ptss": "",
		"trsp": "",
		"beShelfId": "",
		"recall_set": "",
		"module_search": "",
		"min_price": "",
		"max_price": "",
		"storeSlotBooked": "",
		"additionalQueryParams": {
		"hidden_facet": None,
		"translation": None,
		"isMoreOptionsTileEnabled": True,
		"rootDimension": "",
		"altQuery": "",
		"selectedFilter": "",
		"neuralSearchSeeAll": False
		},
		"searchArgs": {
		"query": "",
		"cat_id": "1429",
		"prg": "desktop",
		"facet": ""
		},
		"ffAwareSearchOptOut": False,
		"fitmentFieldParams": {
		"powerSportEnabled": True,
		"dynamicFitmentEnabled": True,
		"extendedAttributesEnabled": True,
		"fuelTypeEnabled": False
		},
		"fitmentSearchParams": {
		"id": "",
		"dealsId": "",
		"query": "",
		"nudgeContext": "",
		"page": page,
		"prg": "desktop",
		"catId": "1429",
		"facet": "",
		"sort": "relevance",
		"rawFacet": "",
		"seoPath": "",
		"ps": 45,
		"limit": 45,
		"ptss": "",
		"trsp": "",
		"beShelfId": "",
		"recall_set": "",
		"module_search": "",
		"min_price": "",
		"max_price": "",
		"storeSlotBooked": "",
		"additionalQueryParams": {
			"hidden_facet": None,
			"translation": None,
			"isMoreOptionsTileEnabled": True,
			"rootDimension": "",
			"altQuery": "",
			"selectedFilter": "",
			"neuralSearchSeeAll": False
		},
		"searchArgs": {
			"query": "",
			"cat_id": "1429",
			"prg": "desktop",
			"facet": ""
		},
		"ffAwareSearchOptOut": False,
		"cat_id": "1429",
		"_be_shelf_id": ""
		},
		"searchParams": {
		"id": "",
		"dealsId": "",
		"query": "",
		"nudgeContext": "",
		"page": page,
		"prg": "desktop",
		"catId": "1429",
		"facet": "",
		"sort": "relevance",
		"rawFacet": "",
		"seoPath": "",
		"ps": 45,
		"limit": 45,
		"ptss": "",
		"trsp": "",
		"beShelfId": "",
		"recall_set": "",
		"module_search": "",
		"min_price": "",
		"max_price": "",
		"storeSlotBooked": "",
		"additionalQueryParams": {
			"hidden_facet": None,
			"translation": None,
			"isMoreOptionsTileEnabled": True,
			"rootDimension": "",
			"altQuery": "",
			"selectedFilter": "",
			"neuralSearchSeeAll": False
		},
		"searchArgs": {
			"query": "",
			"cat_id": "1429",
			"prg": "desktop",
			"facet": ""
		},
		"ffAwareSearchOptOut": False,
		"cat_id": "1429",
		"_be_shelf_id": ""
		},
		"enableFashionTopNav": False,
		"fetchMarquee": True,
		"fetchSkyline": True,
		"fetchSbaTop": True,
		"fetchSBAV1": False,
		"fetchGallery": False,
		"fetchDac": True,
		"enablePortableFacets": True,
		"tenant": "SAMS_GLASS",
		"pageType": "BrowsePage",
		"enableFacetCount": True,
		"enableMultiSave": False,
		"enableInStoreShelfMessage": False,
		"fSeo": True,
		"enableSellerType": False,
		"enableItemRank": False,
		"enableFulfillmentTagsEnhacements": False,
		"enableRxDrugScheduleModal": False,
		"enablePromoData": False,
		"enableAdsPromoData": False,
		"enableSeoLangUrl": False,
		"enableImageBannerCarousel": True,
		"enableHero4": False,
		"enablePromotionMessages": True,
		"enableSignInToSeePrice": True,
		"enableSimpleEmailSignUp": False,
		"enableModuleReposition": True
	}
	})
	headers = {
	'accept': 'application/json',
	'accept-language': 'en-US',
	'baggage': 'trafficType=customer,deviceType=desktop,renderScope=SSR,webRequestSource=Browser,pageName=browseResults,isomorphicSessionId=vPJ6sUZpj7SnuosUQcwMk,renderViewId=c5231973-3b3c-4dbd-8dd6-8dad65a1aabe',
	'content-type': 'application/json',
	'downlink': '10',
	'dpr': '0.8',
	'origin': 'https://www.samsclub.com',
	'priority': 'u=1, i',
	'referer': 'https://www.samsclub.com/browse/shop-all-labor-day/1429?mid=2025_laborday_carouselall_live',
	'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
	'sec-ch-ua-mobile': '?0',
	'sec-ch-ua-platform': '"Windows"',
	'sec-fetch-dest': 'empty',
	'sec-fetch-mode': 'cors',
	'sec-fetch-site': 'same-origin',
	'tenant-id': 'gj9b60',
	'traceparent': '00-18615d84f574ed5b19808ed5c3a172fe-8155daaa8668c196-00',
	'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
	'wm_mp': 'true',
	'wm_page_url': 'https://www.samsclub.com/browse/shop-all-labor-day/1429?mid=2025_laborday_carouselall_live',
	'wm_qos.correlation_id': '3n-RRPa3DdUuyOsH90Lhm3cDvt7LaoTxEhnV',
	'x-apollo-operation-name': 'Browse',
	'x-enable-server-timing': '1',
	'x-latency-trace': '1',
	'x-o-bu': 'SAMS-US',
	'x-o-ccm': 'server',
	'x-o-correlation-id': '3n-RRPa3DdUuyOsH90Lhm3cDvt7LaoTxEhnV',
	'x-o-gql-query': 'query Browse',
	'x-o-mart': 'B2C',
	'x-o-platform': 'rweb',
	'x-o-platform-version': 'samsus-w-1.2.0-77d07fe80e5f61259f5fb0f103c849cd08572ed5-0819',
	'x-o-segment': 'oaoh',
	'Cookie': 'ACID=d91004c0-79ae-414d-8719-878c559ab544; hasACID=true; locGuestData=eyJpbnRlbnQiOiJTSElQUElORyIsImlzRXhwbGljaXQiOmZhbHNlLCJzdG9yZUludGVudCI6IlBJQ0tVUCIsIm1lcmdlRmxhZyI6ZmFsc2UsImlzRGVmYXVsdGVkIjp0cnVlLCJwaWNrdXAiOnsibm9kZUlkIjoiNjM3MiIsInRpbWVzdGFtcCI6MTc1NjQ2NzAzNDQ2OSwic2VsZWN0aW9uVHlwZSI6IkRFRkFVTFRFRCJ9LCJzaGlwcGluZ0FkZHJlc3MiOnsidGltZXN0YW1wIjoxNzU2NDY3MDM0NDY5LCJ0eXBlIjoicGFydGlhbC1sb2NhdGlvbiIsImdpZnRBZGRyZXNzIjpmYWxzZSwicG9zdGFsQ29kZSI6Ijc1MjMxIiwiZGVsaXZlcnlTdG9yZUxpc3QiOlt7Im5vZGVJZCI6IjYzNzIiLCJ0eXBlIjoiREVMSVZFUlkiLCJ0aW1lc3RhbXAiOjE3NTY0NjcwMzQ0NjUsImRlbGl2ZXJ5VGllciI6bnVsbCwic2VsZWN0aW9uVHlwZSI6IkRFRkFVTFRFRCIsInNlbGVjdGlvblNvdXJjZSI6bnVsbH1dLCJjaXR5IjoiRGFsbGFzIiwic3RhdGUiOiJUWCJ9LCJwb3N0YWxDb2RlIjp7InRpbWVzdGFtcCI6MTc1NjQ2NzAzNDQ2OSwiYmFzZSI6Ijc1MjMxIn0sIm1wIjpbXSwibXBEZWxTdG9yZUNvdW50IjowLCJzaG93TG9jYWxFeHBlcmllbmNlIjpmYWxzZSwic2hvd0xNUEVudHJ5UG9pbnQiOmZhbHNlLCJtcFVuaXF1ZVNlbGxlckNvdW50IjowLCJ2YWxpZGF0ZUtleSI6InByb2Q6djI6ZDkxMDA0YzAtNzlhZS00MTRkLTg3MTktODc4YzU1OWFiNTQ0In0=; userAppVersion=samsus-w-1.2.0-77d07fe80e5f61259f5fb0f103c849cd08572ed5-0819; vtc=ULnksPPiOblYLTmWwf05Jk; locale_ab=true; _pxvid=95c9ef32-84cb-11f0-b352-fef928af15d6; __pxvid=95fe3099-84cb-11f0-9bca-9a089b800715; QuantumMetricUserID=c6e7eafed4a11ca83ec8bda1fc4c3972; AZ_ST_CART=68%3A17%23695018394%237%3D1035846401_1756467040372; dimensionData=1597; sxp-rl-SAT_CME-rn=82; sxp-rl-SAT_DISABLE_SYN_PREQUALIFY-rn=33; sxp-rl-SAT_GEO_LOC-rn=14; sxp-rl-SAT_NEW_ORDERS_UI-rn=22; sxp-rl-SAT_ORDER_REPLACEMENT-rn=79; sxp-rl-SAT_REORDER_V4-rn=61; sxp-rl-SCR_CANCEL_ORDER_V3-rn=4; sxp-rl-SCR_CANRV4-rn=68; sxp-rl-SCR_NEXT3-rn=96; sxp-rl-SCR_OHLIMIT-rn=71; sxp-rl-SCR_SHAPEJS-rn=66; sxp-rl-SCR_VERIFICATION_V4-rn=64; sxp-rl-SAT_ADD_ITEM-rn=37; sxp-rl-SCR_RYE-rn=97; sxp-rl-SCR_SCRE-rn=95; sxp-rl-SCR_TII-rn=49; SAT_WPWCNP=1; bstc=VHA5cDsa0F-sLwFSFXhdAA; xpa=FOhdK|IS8qN|Z42C9; exp-ck=FOhdK1IS8qN3; SAMS_GLASS=1; SAT_FGT_PWD=1; isoLoc=US_WA; sxp-rl-SAT_CME-c=r|1|100; SAT_CME=1; sxp-rl-SAT_DISABLE_SYN_PREQUALIFY-c=r|1|0; SAT_DISABLE_SYN_PREQUALIFY=0; sxp-rl-SAT_GEO_LOC-c=r|1|50; SAT_GEO_LOC=1; sxp-rl-SAT_NEW_ORDERS_UI-c=r|1|0; SAT_NEW_ORDERS_UI=0; sxp-rl-SAT_ORDER_REPLACEMENT-c=r|1|0; SAT_ORDER_REPLACEMENT=0; sxp-rl-SAT_REORDER_V4-c=r|1|0; SAT_REORDER_V4=0; sxp-rl-SCR_CANCEL_ORDER_V3-c=r|1|0; SCR_CANCEL_ORDER_V3=0; sxp-rl-SCR_CANRV4-c=r|1|100; SCR_CANRV4=1; sxp-rl-SCR_NEXT3-c=r|1|100; SCR_NEXT3=1; sxp-rl-SCR_OHLIMIT-c=r|1|0; SCR_OHLIMIT=0; sxp-rl-SCR_SHAPEJS-c=r|1|0; SCR_SHAPEJS=0; sxp-rl-SCR_VERIFICATION_V4-c=r|1|0; SCR_VERIFICATION_V4=0; sxp-rl-SAT_ADD_ITEM-c=r|1|100; SAT_ADD_ITEM=1; sxp-rl-SCR_RYE-c=r|1|100; SCR_RYE=1; sxp-rl-SCR_SCRE-c=r|1|100; SCR_SCRE=1; sxp-rl-SCR_TII-c=r|1|100; SCR_TII=1; AMCVS_B98A1CFE53309C340A490D45%40AdobeOrg=1; SSLB=0; s_ecid=MCMID%7C04111747501192365972308737921176565146; AMCV_B98A1CFE53309C340A490D45%40AdobeOrg=1585540135%7CMCIDTS%7C20334%7CMCMID%7C04111747501192365972308737921176565146%7CMCAAMLH-1757392908%7C9%7CMCAAMB-1757392908%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1756795308s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.0; s_cc=true; s_sq=samclub3prod%3D%2526c.%2526a.%2526activitymap.%2526page%253Derror%25253Aerror%2526link%253DGo%252520to%252520our%252520homepage%2526region%253DBODY%2526pageIDType%253D1%2526.activitymap%2526.a%2526.c%2526pid%253Derror%25253Aerror%2526pidt%253D1%2526oid%253Dhttps%25253A%25252F%25252Fwww.samsclub.com%25252F%25253Fxid%25253Derr_go-to-hp%2526ot%253DA; mhmd=ETCN^@lastupd:0|ETSN^@lastupd:0|ATSN^@lastupd:0; locDataV3=eyJpc0RlZmF1bHRlZCI6dHJ1ZSwiaXNFeHBsaWNpdCI6ZmFsc2UsImludGVudCI6IlNISVBQSU5HIiwicGlja3VwIjpbeyJub2RlSWQiOiI2MzcyIiwiZGlzcGxheU5hbWUiOiJEYWxsYXMgU2FtJ3MgQ2x1YiIsImFkZHJlc3MiOnsicG9zdGFsQ29kZSI6Ijc1MjMxIiwiYWRkcmVzc0xpbmUxIjoiNjE4NSBSRVRBSUwgUkQgU1RFIDEwMCIsImNpdHkiOiJEYWxsYXMiLCJzdGF0ZSI6IlRYIiwiY291bnRyeSI6IlVTIn0sImdlb1BvaW50Ijp7ImxhdGl0dWRlIjozMi44NjI4NTgsImxvbmdpdHVkZSI6LTk2Ljc1NDQ2NX0sInNjaGVkdWxlZEVuYWJsZWQiOmZhbHNlLCJ1blNjaGVkdWxlZEVuYWJsZWQiOmZhbHNlLCJzdG9yZUhycyI6IjEwOjAwLTIwOjAwIiwic3VwcG9ydGVkQWNjZXNzVHlwZXMiOlsiUElDS1VQX0lOU1RPUkUiLCJQSUNLVVBfQ1VSQlNJREUiXSwidGltZVpvbmUiOiJBbWVyaWNhL0NoaWNhZ28iLCJzdG9yZUJyYW5kRm9ybWF0IjoiU2FtJ3MgQ2x1YiIsInNlbGVjdGlvblR5cGUiOiJERUZBVUxURUQifV0sInNoaXBwaW5nQWRkcmVzcyI6eyJsYXRpdHVkZSI6MzIuODc5ODA3MSwibG9uZ2l0dWRlIjotOTYuNzU0NzUyMjAwMDAwMDEsInBvc3RhbENvZGUiOiI3NTIzMSIsImNpdHkiOiJEYWxsYXMiLCJzdGF0ZSI6IlRYIiwiY291bnRyeUNvZGUiOiJVU0EiLCJnaWZ0QWRkcmVzcyI6ZmFsc2UsInRpbWVab25lIjoiQW1lcmljYS9DaGljYWdvIn0sImFzc29ydG1lbnQiOnsibm9kZUlkIjoiNjM3MiIsImRpc3BsYXlOYW1lIjoiRGFsbGFzIFNhbSdzIENsdWIiLCJpbnRlbnQiOiJQSUNLVVAifSwiaW5zdG9yZSI6ZmFsc2UsImRlbGl2ZXJ5Ijp7Im5vZGVJZCI6IjYzNzIiLCJkaXNwbGF5TmFtZSI6IkRhbGxhcyBTYW0ncyBDbHViIiwiYWRkcmVzcyI6eyJwb3N0YWxDb2RlIjoiNzUyMzEiLCJhZGRyZXNzTGluZTEiOiI2MTg1IFJFVEFJTCBSRCBTVEUgMTAwIiwiY2l0eSI6IkRhbGxhcyIsInN0YXRlIjoiVFgiLCJjb3VudHJ5IjoiVVMifSwiZ2VvUG9pbnQiOnsibGF0aXR1ZGUiOjMyLjg2Mjg1OCwibG9uZ2l0dWRlIjotOTYuNzU0NDY1fSwidHlwZSI6IkRFTElWRVJZIiwic2NoZWR1bGVkRW5hYmxlZCI6ZmFsc2UsInVuU2NoZWR1bGVkRW5hYmxlZCI6ZmFsc2UsImFjY2Vzc1BvaW50cyI6W3siYWNjZXNzVHlwZSI6IkRFTElWRVJZX0FERFJFU1MifV0sImlzRXhwcmVzc0RlbGl2ZXJ5T25seSI6ZmFsc2UsInN1cHBvcnRlZEFjY2Vzc1R5cGVzIjpbIkRFTElWRVJZX0FERFJFU1MiXSwidGltZVpvbmUiOiJBbWVyaWNhL0NoaWNhZ28iLCJzdG9yZUJyYW5kRm9ybWF0IjoiU2FtJ3MgQ2x1YiIsInNlbGVjdGlvblR5cGUiOiJERUZBVUxURUQifSwiaXNnZW9JbnRsVXNlciI6ZmFsc2UsIm1wRGVsU3RvcmVDb3VudCI6MCwicmVmcmVzaEF0IjoxNzU2NzkxNzEzMzk1LCJ2YWxpZGF0ZUtleSI6InByb2Q6djI6ZDkxMDA0YzAtNzlhZS00MTRkLTg3MTktODc4YzU1OWFiNTQ0In0=; assortmentStoreId=6372; _shcc=US; _intlbu=false; hasLocData=1; xpm=1%2B1756788109%2BULnksPPiOblYLTmWwf05Jk~%2B1; bm_mi=3E7D432BCFE1B2BB02AD99BEA4BAB546~YAAQbNAuFzcyK/CYAQAABkW7CBywDqwdp/f5EOuEFd2B8WaYTFsQkZLclEtzfv/9TxCKNbV2+ghHZ/p9vo1JbncnvoSUCTtUl9arnCawQhb/O+SbGlGNOnG+ibTpkTHEH4oCBFES8h5pmFK66xN+ovDx5rJ3V3nQdWm0/q2xYwefH5YLZE+8xOx6EIZwRToj+k4qyuX5EaGSE4iO5K2gBZNaNNT0qcHSYK7HUOyNpG8mxdsXstLOXaWWqn64V/6Zf5lq6GgWgEv3Z4GnVzpQ+QQlHgvYnZ3vDbck5B+cgwW8Fqem8mF+Cccsgdha668=~1; pxcts=278604fc-87b7-11f0-89d5-813a57d43da1; _astc=4cde8c295891c1b4cf2af5c412e344ec; adblocked=false; ak_bmsc=9AC6FDFDCFC4611223D193EDF6EB63A4~000000000000000000000000000000~YAAQbNAuF7E2K/CYAQAAslC7CBxgM7Cs2+E7CGI14g7AtnaSYXD8vw9RjoDA4PWm8e4vA1qb2A0h/GuROeykyJ1K7tMR73WhNcIsRhjzLLIQbSt8zwuxaNFUq/c9IjgXHumACRZ0yvuVgXCdE8D+dF/2YS8oeW3gAKEvtkVWFaVRgBrSAuUy5mneutmUfhd1sEpkUhww3YXBieKUhaZgz0OPh0L4Ek70JHgiaB2VjFIVToeOIH5XU8mB73xfN+FzoHYDURMmMvnLGvAy1N8QZbLHjyvDAxewooPNERtCb0EXXfZS9a19wbtgFEuRX3zymCmOqxazLUuSWaaBjGYsewE2vLqOOlOV+zQXxJ1IU6YlMYz0GabQF1Zi04Hvwap8In6UrI5gEmEZq21VSBjvJdtl79L2T3Nu0lyob8U2hLum0Qs32C/UnZs6a65/hf9eXnvknuYUu0a5AxnutLEtQSdvoaqy4zsCRvBQp+yur/E=; __gads=ID=7a80d931767f6f1d:T=1756467040:RT=1756788119:S=ALNI_MbSKep3ssTfZdrsFjeSz5nhZpqLPA; __gpi=UID=0000118889ae2c48:T=1756467040:RT=1756788119:S=ALNI_MY5koa0Zjr1QLyhRVW_w3Dy4aLkGA; __eoi=ID=8290d3dd0dde7f46:T=1756467040:RT=1756788119:S=AA-AfjaVGPnI3CZ2XEuUSgxygz1U; QuantumMetricSessionID=823336a5eb1734e4abb71e2e75c16af3; SCR_PDP_NST=0; seqnum=13; TS017c4a41=01178efe2587e2b6cf8b1e0f7fb4edf8733b610b0973a8f00288712cc45f406c8f36ea4dc5fe70ed3b9211ec572ea4b08dfd05bc04; TS01b1959a=01178efe2587e2b6cf8b1e0f7fb4edf8733b610b0973a8f00288712cc45f406c8f36ea4dc5fe70ed3b9211ec572ea4b08dfd05bc04; TSbdf847b3027=08a428dbeeab2000c6566b34d76595717093ca77f89df278e582a7c3487348d88fc1c16f97d2786308a28b2883113000e63b1f187064c365935367103c8138ec6413ea5566e8f1097f107399284b7f2f2945db303ca56520988ff0e63a49a57b; akavpau_P1_Sitewide=1756788759~id=f2a0f345d7e255de647fdfb2e19c8402; _px3=871c21553f88535789cc8e51f0e0ccb1b3a13572c8248247a61488c871d2820f:QFURpc2zwi+59nw0ttfrPorVrDYA5Jk3dHEdEEiYTVlJqY1Jrs2bmd5FIyrnyWD8ZFPriObJGfVlSJb0fJ7Gug==:1000:Sbx3fhlw+LyFdt3TyyU002isTIAlLH7CeEWtRGVI6sUJIIq9NQTa1kxQq2tCh/h8RclnCzGxMoCwDoNBrwxv2h++Z0lUXw66cwzMIxcHG+NvDiIKDs4JO/CtmiQGheq5+at62dM6HfAwCWcQwweS+VQ06hHj1LiFdoLQWS8eOGnemo88PylDmPjdkULyIDFBqrdTP/llp1UXnJvZEnon2iyBRMjzRleUM2s9Ikc7lIw=; _pxde=ec13cdf7d3eddf73f3000bce1f7b4112e7cdb38d41fcb0a8b813931efd94e76a:eyJ0aW1lc3RhbXAiOjE3NTY3ODgxNTk2ODl9; xptwj=js:ac5c0fc8d65edcd37ae6:E9Aqs4OmZflpMeKl9gQgkYZPDQ2rN/UUF5ZWuCyCko67kUtU6NlnXk6RrIBRhPwPpB+Aqv68kf23mob73RWqaZY8WAbmZJUJQCgkCbJOLaaHpcfHR5LlinXh8RI=; TS017260c8=01fc5982040ff9e1fbe41ebdd8ba862e17f2538321f87b1bb4ac2c2f7fafa099da3e38a52a8ebd734ee8bc20842f386002f09ff49a; bm_sv=9EED3612B52E558151A7BE5A616C8E69~YAAQbNAuFyx0K/CYAQAAS/W7CBwznw4a3F60WcOHFVCwliZrXB6A16bBz1GK4PhFNLsbiBhbSGxh/BjbijwaQ4gGYpR5O+nCyENxdKPmeTCVGkBXKuHQsSyEU5H/en/whqZDbfZCzB+hk316fTri0n0D5m+fhoWinbSjbwzUJvhAtVRGRFZ+oA6xDXLOCLzu6N9Id/fvGghy8M2ZyUJjaPAykiGAhXOBhayef9faPVJWAtl96rbOsZiwUHcIo1/CZqHm~1; TS017260c8=01a0cb2bf63fcd810296ac6afdd7423873f4d9b84df4cf413fc5db154a042eae86448bc45b4285246964a7a5be7c2590bc064efaef; TS01b1959a=01a0cb2bf63fcd810296ac6afdd7423873f4d9b84df4cf413fc5db154a042eae86448bc45b4285246964a7a5be7c2590bc064efaef; bm_sv=9EED3612B52E558151A7BE5A616C8E69~YAAQbNAuF4xCLvCYAQAAbwjDCBwieB402yVZm5jM4NeVFJVu4r+ezViINxTQ5qznHN/oWx/Caf/UgeR61t0y9/Bh2Z46wk78MyjO3Zh2ZvzpJzQUv7lILEpy8Hc7952ptWLjrqi9Xt82n4B3F/pBpmBgcy0flYOButzuTUTSoecnU3AU+j6qfO2qnvH7fhY2YtyRgKM1b8nCgPx19HpeL1xU+wRRLnl2rOPWAaJbKwwX13vZ6ynQF4V3s3A41ucn2rkX~1; bstc=VHA5cDsa0F-sLwFSFXhdAA; exp-ck=FOhdK1IS8qN3; seqnum=14; vtc=ULnksPPiOblYLTmWwf05Jk; xpa=FOhdK|IS8qN|Z42C9; xpm=1%2B1756788109%2BULnksPPiOblYLTmWwf05Jk~%2B1; TS017c4a41=01a0cb2bf63fcd810296ac6afdd7423873f4d9b84df4cf413fc5db154a042eae86448bc45b4285246964a7a5be7c2590bc064efaef; TSbdf847b3027=088d8668f3ab2000057ed96c0feb3dcf1a418cb50fcb828d17d337b6e1b24f7d54fc9c8ce05316dd080ebbf17711300001099b0f702c1fac43d8cb07fd87ef6d755b46d91248197c30bc07d8b7eddf1d0710263a368e0f41216e9f3980219b68; akavpau_P1_Sitewide=1756789223~id=3575e6bb11105f0626565b288223ff3b; isoLoc=US_WA; locale_ab=true'
	}

	response = requests.request("POST", url, headers=headers, data=payload)

	for item in response.json()['data']['search']['searchResult']['itemStacks'][0]['itemsV2']:
		try:
			souce_url = 'https://www.samsclub.com'+item['canonicalUrl']
			urls.append(souce_url)
		except:
			continue

def get_product_info(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	data_json = soup.find('script', {'data-seo-id': 'schema-org-product'}).get_text()
	data_json = json.loads(data_json)

	upc = data_json['gtin13']
	price = data_json['offers'][0]['priceSpecification'][-1]['price']

	with counter_lock:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([upc, price, link])


if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/45)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')