export type VRT_NODE = {
  __typename: string, // EpisodeTile
  available: boolean,
  objectId: string,
  description: string,
  title: string,
  active: boolean,
  image: {
    templateUrl: string,
  },
  episode: {
    objectId: string,
    program: {
      link: string,
      objectId: string,
    },
  },
  primaryMeta: {
    longValue: string,
    shortValue: string,
    type: string,
    value: string,
  }[],
  playAction: {
    pageUrl: string,
  },
  formattedDuration: string,
  link: string,
}
export type VRT_EDGE = {
  cursor: string,
  node: VRT_NODE,
};
export type VRT_PAGINATED_ITEMS = {
  pageInfo: VRT_PAGE_INFO,
  edges: VRT_EDGE[],
};

export type VRT_COMPONENT = {
  __typename: string,
  objectId: string,
  items: VRT_ITEM[],
  title: string,
  listId: string,
  description: string,
  paginatedItems: VRT_PAGINATED_ITEMS,
};
export type VRT_ITEM = {
  objectId: string,
  active: boolean,
  title: string,
  components: VRT_COMPONENT[],
};
export type VRT_PAGE_INFO = {
  endCursor: string,
  hasNextPage: boolean,
  hasPreviousPage: boolean,
  startCursor: string,
};

export type SearchResultResponse = {
  data: {
    list: {
      paginatedItems: VRT_PAGINATED_ITEMS,
    },
  },
};

export const getProgramsQuery = `
  query PaginatedTileListPage($listId: ID!, $lazyItemCount: Int = 30, $after: ID, $before: ID) {
    list(listId: $listId) {
      __typename
      ... on PaginatedTileList {
        ...paginatedTileListFragment
        __typename
      }
    }
  }
  fragment imageFragment on Image {
    __typename
    objectId
    alt
    title
    focalPoint
    templateUrl
  }
  fragment tileFragment on Tile {
    ... on IIdentifiable {
      __typename
      objectId
    }
    ... on IComponent {
      __typename
    }
    ... on ITile {
      description
      title
      active
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
      indexMeta {
        __typename
        type
        value
      }
      statusMeta {
        __typename
        type
        value
      }
      labelMeta {
        __typename
        type
        value
      }
      __typename
    }
    ... on ContentTile {
      brand
      __typename
    }
    ... on BannerTile {
      compactLayout
      backgroundColor
      textTheme
      brand
      ctaText
      passUserIdentity
      titleArt {
        objectId
        templateUrl
        __typename
      }
      __typename
    }
    ... on EpisodeTile {
      description
      formattedDuration
      available
      chapterStart
      playAction: watchAction {
        pageUrl: videoUrl
        resumePointProgress
        resumePointTotal
        completed
        __typename
      }
      episode {
        __typename
        objectId
        program {
          __typename
          objectId
          link
        }
      }
      epgDuration
      __typename
    }
    ... on PodcastEpisodeTile {
      formattedDuration
      available
      programLink: podcastEpisode {
        objectId
        podcastProgram {
          objectId
          link
          __typename
        }
        __typename
      }
      playAction: listenAction {
        pageUrl: podcastEpisodeLink
        resumePointProgress
        resumePointTotal
        completed
        __typename
      }
      __typename
    }
    ... on PodcastProgramTile {
      link
      __typename
    }
    ... on ProgramTile {
      link
      __typename
    }
    ... on AudioLivestreamTile {
      brand
      brandsLogos {
        brand
        brandTitle
        __typename
      }
      __typename
    }
    ... on LivestreamTile {
      description
      __typename
    }
    ... on ButtonTile {
      icon
      iconPosition
      mode
      __typename
    }
    ... on RadioEpisodeTile {
      available
      epgDuration
      formattedDuration
      thumbnailMeta {
        ...metaFragment
        __typename
      }
      __typename
    }
    ... on SongTile {
      startDate
      formattedStartDate
      endDate
      __typename
    }
    ... on RadioProgramTile {
      objectId
      __typename
    }
  }
  fragment metaFragment on MetaDataItem {
    __typename
    type
    value
    shortValue
    longValue
  }
  fragment paginatedTileListFragment on PaginatedTileList {
    __typename
    objectId
    listId
    banner {
      backgroundColor
      compactLayout
      description
      image {
        ...imageFragment
        __typename
      }
      textTheme
      title
      __typename
    }
    bannerSize
    displayType
    expires
    tileVariant
    paginatedItems(first: $lazyItemCount, after: $after, before: $before) {
      __typename
      edges {
        __typename
        cursor
        node {
          __typename
          ...tileFragment
        }
      }
      pageInfo {
        __typename
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
      }
    }
    sort {
      icon
      order
      title
      __typename
    }
    tileContentType
    tileOrientation
    title
    description
    ... on IComponent {
      __typename
    }
  }
`;

export type ProgramResponse = {
  data: {
    page: {
      components: VRT_COMPONENT[],
    }
  }
};

export const getSingleProgramQuery = `
  query VideoProgramPage($pageId: ID!, $lazyItemCount: Int = 10, $after: ID, $before: ID) {
    page(id: $pageId) {
      ... on ProgramPage {
        objectId
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
        components {
          __typename
          ... on IComponent {
            ...componentTrackingDataFragment
            __typename
          }
          ... on Banner {
            ...bannerFragment
            __typename
          }
          ... on PageHeader {
            ...pageHeaderFragment
            __typename
          }
          ... on ContainerNavigation {
            objectId
            navigationType
            items {
              objectId
              title
              active
              components {
                __typename
                ... on IComponent {
                  ...componentTrackingDataFragment
                  __typename
                }
                ... on PaginatedTileList {
                  ...paginatedTileListFragment
                  __typename
                }
                ... on StaticTileList {
                  ...staticTileListFragment
                  __typename
                }
                ... on LazyTileList {
                  objectId
                  title
                  listId
                  __typename
                }
                ... on Banner {
                  ...bannerFragment
                  __typename
                }
                ... on IComponent {
                  ... on Text {
                    ...textFragment
                    __typename
                  }
                  ... on TagsList {
                    objectId
                    title
                    tags {
                      name
                      title
                      category
                      __typename
                    }
                    __typename
                  }
                  ... on PresentersList {
                    objectId
                    title
                    presenters {
                      title
                      type
                      __typename
                    }
                    __typename
                  }
                  ... on ContainerNavigation {
                    objectId
                    navigationType
                    items {
                      objectId
                      title
                      components {
                        __typename
                        ... on Component {
                          ... on PaginatedTileList {
                            ...paginatedTileListFragment
                            __typename
                          }
                          ... on StaticTileList {
                            ...staticTileListFragment
                            __typename
                          }
                          ... on LazyTileList {
                            objectId
                            title
                            listId
                            __typename
                          }
                          __typename
                        }
                      }
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
              }
              __typename
            }
            __typename
          }
          ...paginatedTileListFragment
        }
        __typename
      }
      __typename
    }
  }
  fragment metaFragment on MetaDataItem {
    __typename
    type
    value
    shortValue
    longValue
  }
  fragment staticTileListFragment on StaticTileList {
    __typename
    objectId
    listId
    title
    description
    tileContentType
    tileOrientation
    displayType
    expires
    tileVariant
    sort {
      icon
      order
      title
      __typename
    }
    actionItems {
      ...actionItemFragment
      __typename
    }
    banner {
      actionItems {
        ...actionItemFragment
        __typename
      }
      description
      image {
        ...imageFragment
        __typename
      }
      compactLayout
      backgroundColor
      textTheme
      title
      titleArt {
        objectId
        templateUrl
        __typename
      }
      __typename
    }
    bannerSize
    items {
      ...tileFragment
      __typename
    }
    ... on IComponent {
      ...componentTrackingDataFragment
      __typename
    }
  }
  fragment actionItemFragment on ActionItem {
    __typename
    objectId
    accessibilityLabel
    action {
      ...actionFragment
      __typename
    }
    active
    icon
    iconPosition
    icons {
      __typename
      position
      ... on DesignSystemIcon {
        value {
          name
          __typename
        }
        __typename
      }
    }
    mode
    objectId
    title
  }
  fragment actionFragment on Action {
    __typename
    ... on FavoriteAction {
      favorite
      id
      programUrl
      programWhatsonId
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
    ... on PodcastEpisodeListenAction {
      id: audioId
      podcastEpisodeLink
      resumePointProgress
      resumePointTotal
      completed
      __typename
    }
    ... on EpisodeWatchAction {
      id: videoId
      videoUrl
      resumePointProgress
      resumePointTotal
      completed
      __typename
    }
    ... on LinkAction {
      id: linkId
      linkId
      link
      linkType
      openExternally
      passUserIdentity
      linkTokens {
        __typename
        placeholder
        value
      }
      __typename
    }
    ... on ShareAction {
      title
      url
      __typename
    }
    ... on SwitchTabAction {
      referencedTabId
      mediaType
      link
      __typename
    }
    ... on RadioEpisodeListenAction {
      streamId
      pageLink
      startDate
      __typename
    }
    ... on LiveListenAction {
      streamId
      livestreamPageLink
      startDate
      endDate
      __typename
    }
    ... on LiveWatchAction {
      streamId
      livestreamPageLink
      startDate
      endDate
      __typename
    }
  }
  fragment imageFragment on Image {
    __typename
    objectId
    alt
    title
    focalPoint
    templateUrl
  }
  fragment tileFragment on Tile {
    ... on IIdentifiable {
      __typename
      objectId
    }
    ... on IComponent {
      ...componentTrackingDataFragment
      __typename
    }
    ... on ITile {
      description
      title
      active
      action {
        ...actionFragment
        __typename
      }
      actionItems {
        ...actionItemFragment
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
      indexMeta {
        __typename
        type
        value
      }
      statusMeta {
        __typename
        type
        value
      }
      labelMeta {
        __typename
        type
        value
      }
      __typename
    }
    ... on ContentTile {
      brand
      brandLogos {
        ...brandLogosFragment
        __typename
      }
      __typename
    }
    ... on BannerTile {
      compactLayout
      backgroundColor
      textTheme
      brand
      brandLogos {
        ...brandLogosFragment
        __typename
      }
      ctaText
      passUserIdentity
      titleArt {
        objectId
        templateUrl
        __typename
      }
      __typename
    }
    ... on EpisodeTile {
      description
      formattedDuration
      available
      chapterStart
      action {
        ...actionFragment
        __typename
      }
      playAction: watchAction {
        pageUrl: videoUrl
        resumePointProgress
        resumePointTotal
        completed
        __typename
      }
      episode {
        __typename
        objectId
        program {
          __typename
          objectId
          link
        }
      }
      epgDuration
      __typename
    }
    ... on PodcastEpisodeTile {
      formattedDuration
      available
      programLink: podcastEpisode {
        objectId
        podcastProgram {
          objectId
          link
          __typename
        }
        __typename
      }
      playAction: listenAction {
        pageUrl: podcastEpisodeLink
        resumePointProgress
        resumePointTotal
        completed
        __typename
      }
      __typename
    }
    ... on PodcastProgramTile {
      link
      __typename
    }
    ... on ProgramTile {
      link
      __typename
    }
    ... on AudioLivestreamTile {
      brand
      brandsLogos {
        brand
        brandTitle
        logos {
          ...brandLogosFragment
          __typename
        }
        __typename
      }
      __typename
    }
    ... on LivestreamTile {
      description
      __typename
    }
    ... on ButtonTile {
      icon
      iconPosition
      mode
      __typename
    }
    ... on RadioEpisodeTile {
      action {
        ...actionFragment
        __typename
      }
      available
      epgDuration
      formattedDuration
      thumbnailMeta {
        ...metaFragment
        __typename
      }
      ...componentTrackingDataFragment
      __typename
    }
    ... on SongTile {
      startDate
      formattedStartDate
      endDate
      __typename
    }
    ... on RadioProgramTile {
      objectId
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
  }
  fragment brandLogosFragment on Logo {
    colorOnColor
    height
    mono
    primary
    type
    width
  }
  fragment paginatedTileListFragment on PaginatedTileList {
    __typename
    objectId
    listId
    actionItems {
      ...actionItemFragment
      __typename
    }
    banner {
      actionItems {
        ...actionItemFragment
        __typename
      }
      backgroundColor
      compactLayout
      description
      image {
        ...imageFragment
        __typename
      }
      textTheme
      title
      __typename
    }
    bannerSize
    displayType
    expires
    tileVariant
    paginatedItems(first: $lazyItemCount, after: $after, before: $before) {
      __typename
      edges {
        __typename
        cursor
        node {
          __typename
          ...tileFragment
        }
      }
      pageInfo {
        __typename
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
      }
    }
    sort {
      icon
      order
      title
      __typename
    }
    tileContentType
    tileOrientation
    title
    description
    ... on IComponent {
      ...componentTrackingDataFragment
      __typename
    }
  }
  fragment pageHeaderFragment on PageHeader {
    objectId
    title
    richShortDescription {
      __typename
      html
    }
    richDescription {
      __typename
      html
    }
    announcementValue
    announcementType
    mostRelevantEpisodeTile {
      __typename
      objectId
      tile {
        ...tileFragment
        __typename
      }
      title
    }
    actionItems {
      ...actionItemFragment
      __typename
    }
    secondaryMeta {
      longValue
      shortValue
      type
      value
      __typename
    }
    image {
      objectId
      alt
      focalPoint
      templateUrl
      __typename
    }
    categories {
      category
      name
      title
      __typename
    }
    presenters {
      title
      __typename
    }
    brands {
      name
      title
      __typename
    }
    brandsLogos {
      brand
      brandTitle
      logos {
        mono
        primary
        type
        __typename
      }
      __typename
    }
  }
  fragment bannerFragment on Banner {
    __typename
    objectId
    brand
    countdown {
      date
      __typename
    }
    richDescription {
      __typename
      text
    }
    ctaText
    image {
      objectId
      templateUrl
      alt
      focalPoint
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
    ... on IComponent {
      ...componentTrackingDataFragment
      __typename
    }
  }
  fragment textFragment on Text {
    __typename
    objectId
    html
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
  }
`;

export type MoreSeasonsResponse = {
  data: {
    list: {
      listId: string,
      objectId: string,
      items: VRT_NODE[],
    },
  },
};
