VRTMAX_graphql_query = '''
  query EpisodePage($pageId: ID!) {
    page(id: $pageId) {
      ... on PlaybackPage {
        ...playbackPageFragment
        __typename
      }
      ... on RadioEpisodePage {
        header {
          title
          announcementValue
          brandsLogos {
            brandTitle
            logos {
              type
              mono
              width
              height
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      ...errorFragment
      __typename
    }
  }
  
  fragment playbackPageFragment on PlaybackPage {
    __typename
    objectId
    title
    brand
    brandLogos {
      ...brandLogosFragment
      __typename
    }
    permalink
    seo {
      ...seoFragment
      __typename
    }
    socialSharing {
      ...socialSharingFragment
      __typename
    }
    trackingData {
      ...trackingDataFragment
      __typename
    }
    ldjson
    player {
      ...playerFragment
      __typename
    }
    menu {
      ...menuFragment
      __typename
    }
    popUp: nudge {
      ...popupFragment
      __typename
    }
    toast: nudge {
      ...toastFragment
      __typename
    }
    components {
      ...bannerFragment
      ...contactInfoFragment
      ...mediaInfoFragment
      __typename
    }
  }
  
  fragment menuFragment on ContainerNavigation {
    __typename
    objectId
    accessibilityTitle
    items {
      __typename
      objectId
      componentId
      title
      active
      action {
        ... on SwitchTabAction {
          __typename
          referencedTabId
          link
        }
        __typename
      }
    }
  }
  
  fragment seoFragment on SeoProperties {
    __typename
    title
    description
  }
  
  fragment socialSharingFragment on SocialSharingProperties {
    __typename
    title
    description
    image {
      __typename
      objectId
      templateUrl
    }
  }
  
  fragment playerFragment on MediaPlayer {
    __typename
    objectId
    classification {
      iconName
      __typename
    }
    maxAge
    image {
      ...imageFragment
      __typename
    }
    modes {
      __typename
      active
      adsUrl
      cimMediaTrackingData {
        channel
        ct
        programDuration
        programId
        programName
        se
        st
        tv
        __typename
      }
      mediaTrackingData {
        ...trackingDataFragment
        __typename
      }
      token {
        placeholder
        value
        __typename
      }
      resumePointTemplate {
        mediaId
        mediaName
        __typename
      }
      streamId
      ... on VideoPlayerMode {
        aspectRatio
        __typename
      }
      ... on AudioPlayerMode {
        broadcastStartDate
        __typename
      }
    }
    progress {
      __typename
      completed
      durationInSeconds
      progressInSeconds
    }
    secondaryMeta {
      ...metaFragment
      __typename
    }
    subtitle
    title
  }
  
  fragment imageFragment on Image {
    __typename
    objectId
    alt
    focusPoint {
      x
      y
      __typename
    }
    templateUrl
  }
  
  fragment metaFragment on MetaDataItem {
    __typename
    type
    value
    shortValue
    longValue
  }
  
  fragment trackingDataFragment on PageTrackingData {
    data
    perTrigger {
      trigger
      data
      template {
        id
        __typename
      }
      __typename
    }
    __typename
  }
  
  fragment bannerFragment on Banner {
    __typename
    objectId
    accessibilityTitle
    brand
    countdown {
      date
      __typename
    }
    richDescription {
      __typename
      text
    }
    image {
      objectId
      templateUrl
      alt
      focusPoint {
        x
        y
        __typename
      }
      __typename
    }
    title
    compactLayout
    textTheme
    backgroundColor
    style
    action {
      ...actionFragment
      __typename
    }
    actionItems {
      ...actionItemFragment
      __typename
    }
    titleArt {
      objectId
      templateUrl
      __typename
    }
    labelMeta {
      __typename
      type
      value
    }
    preview {
      video {
        objectId
        modes {
          __typename
          streamId
        }
        __typename
      }
      __typename
    }
    ... on IComponent {
      ...componentTrackingDataFragment
      __typename
    }
  }
  
  fragment actionFragment on Action {
    __typename
    ... on FavoriteAction {
      id
      favorite
      title
      __typename
    }
    ... on ListDeleteAction {
      listName
      id
      listId
      title
      __typename
    }
    ... on ListTileDeletedAction {
      listName
      id
      listId
      __typename
    }
    ... on LinkAction {
      internalTarget
      link
      internalTarget
      externalTarget
      passUserIdentity
      zone {
        preferredZone
        isExclusive
        __typename
      }
      linkTokens {
        __typename
        placeholder
        value
      }
      __typename
    }
    ... on ClientDrivenAction {
      __typename
      clientDrivenActionType
    }
    ... on ShareAction {
      title
      url
      __typename
    }
    ... on SwitchTabAction {
      referencedTabId
      link
      __typename
    }
    ... on FinishAction {
      id
      __typename
    }
  }
  
  fragment actionItemFragment on ActionItem {
    __typename
    objectId
    accessibilityLabel
    active
    mode
    title
    themeOverride
    action {
      ...actionFragment
      __typename
    }
    icons {
      ...iconFragment
      __typename
    }
  }
  
  fragment iconFragment on Icon {
    __typename
    accessibilityLabel
    position
    type
    ... on DesignSystemIcon {
      value {
        __typename
        color
        name
      }
      activeValue {
        __typename
        color
        name
      }
      __typename
    }
    ... on ImageIcon {
      value {
        __typename
        srcSet {
          src
          format
          __typename
        }
      }
      activeValue {
        __typename
        srcSet {
          src
          format
          __typename
        }
      }
      __typename
    }
  }
  
  fragment componentTrackingDataFragment on IComponent {
    trackingData {
      data
      perTrigger {
        trigger
        data
        template {
          id
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
  
  fragment brandLogosFragment on Logo {
    colorOnColor
    height
    mono
    primary
    type
    width
    __typename
  }
  
  fragment contactInfoFragment on ContactInfo {
    __typename
    title
    items {
      title
      description
      options {
        objectId
        title
        icons {
          ...iconFragment
          __typename
        }
        action {
          ... on LinkAction {
            link
            externalTarget
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
  }
  
  fragment mediaInfoFragment on MediaInfo {
    __typename
    objectId
    title
    maxAge
    description
    accessibilityTitle
    actionItems {
      ...actionItemFragment
      __typename
    }
    trackingData {
      ...trackingDataFragment
      __typename
    }
    image {
      ...imageFragment
      __typename
    }
    primaryMeta {
      ...metaFragment
      __typename
    }
    secondaryMeta {
      ...metaFragment
      __typename
    }
    tertiaryMeta {
      ...metaFragment
      __typename
    }
    quaternaryMeta {
      label
      ...metaFragment
      __typename
    }
  }
  
  fragment popupFragment on PopUp {
    __typename
    brand
    brandsLogos {
      ...brandLogo
      __typename
    }
    buttons {
      ...actionItemFragment
      __typename
    }
    description
    image {
      ...imageFragment
      __typename
    }
    objectId
    size
    title
    videoStreamId
    trackingData {
      ...trackingDataFragment
      __typename
    }
  }
  
  fragment brandLogo on BrandLogo {
    brand
    brandTitle
    logos {
      type
      primary
      colorOnColor
      __typename
    }
    __typename
  }
  
  fragment toastFragment on Toast {
    __typename
    description
    image {
      ...imageFragment
      __typename
    }
    objectId
    title
  }
  
  fragment errorFragment on ErrorPage {
    errorComponents: components {
      ...noContentFragment
      __typename
    }
    __typename
  }
  
  fragment noContentFragment on NoContent {
    __typename
    objectId
    title
    text
    backgroundImage {
      ...imageFragment
      __typename
    }
    mainImage {
      ...imageFragment
      __typename
    }
    noContentType
    actionItems {
      ...actionItemFragment
      __typename
    }
  }
'''